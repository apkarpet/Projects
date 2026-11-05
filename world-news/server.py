#!/usr/bin/env python3
"""Fantasy Desk: EuroLeague Fantasy tools and basketball scores on localhost.

    python3 server.py            # serve on the port from config.json
    python3 server.py --port N   # override the port
"""

import argparse
import hashlib
import json
import logging
import mimetypes
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from newsdesk import fantasy, optimize, picks, sports
from newsdesk.cache import Cache

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
CONFIG_PATH = os.path.join(ROOT, "config.json")
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "world-news")
# Pre-lock projections are kept for good (not a cache) so each round can be scored later.
TRACK_DIR = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "world-news", "tracking")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("newsdesk")

cache = Cache(os.path.join(CACHE_DIR, "cache.json"))

# ---------------------------------------------------------------- config

_config = {"mtime": 0, "value": None}
_config_lock = threading.Lock()


def config():
    """config.json, reloaded automatically whenever the file changes."""
    with _config_lock:
        mtime = os.path.getmtime(CONFIG_PATH)
        if mtime != _config["mtime"]:
            with open(CONFIG_PATH) as f:
                _config["value"] = json.load(f)
            _config["mtime"] = mtime
            log.info("loaded config.json")
        return _config["value"]


def _digest(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:8]


# ---------------------------------------------------------------- data

LEAGUES = {"euroleague": sports.euroleague, "nba": sports.nba, "gbl": sports.gbl}


def sports_ttl(payload):
    return 60 if sports.has_live(payload) else 10 * 60


def get_league(league, force=False):
    fn = LEAGUES.get(league)
    if fn is None:
        return None
    key = f"sports:{league}"
    data = cache.get(key, sports_ttl, fn, force)
    return {**data, "fetched": cache.fetched_at(key)}


def cached_box(season, game):
    return cache.get(f"box4:{season}:{game['id']}", float("inf"), lambda: fantasy.box_score(season, game))


def get_fantasy(force=False):
    cfg = config()
    el = get_league("euroleague", force)
    season = el.get("season") or sports.el_season()
    out = {"season": season}
    try:
        out["injuries"] = cache.get(
            "fantasy:injuries", 30 * 60, lambda: fantasy.injuries(cfg["injury_report_url"]), force
        )
    except Exception as e:  # noqa: BLE001
        out["injuries"] = None
        out["injuries_error"] = str(e)
    try:
        out["leaders"] = cache.get(f"fantasy:pir:{season}", 30 * 60, lambda: fantasy.pir_leaders(season), force)
    except Exception:  # noqa: BLE001
        out["leaders"] = []
    out["rounds"] = fantasy.round_performers(season, el.get("rounds", []), cached_box)
    out["default"] = el.get("default")
    return out


def get_injuries(force=False):
    cfg = config()
    return cache.get("fantasy:injuries", 30 * 60, lambda: fantasy.injuries(cfg["injury_report_url"]), force)


def picks_inputs(force=False):
    """Everything the projection model reads, from cache where possible."""
    season = sports.el_season()
    games = cache.get(
        f"el:games:{season}",
        lambda gs: 60 if any(g["state"] == "in" for g in gs) else 10 * 60,
        lambda: sports.el_games(season),
        force,
    )
    finished = [g for g in games if g["state"] == "post"]
    list(fantasy._BOX_POOL.map(lambda g: cached_box(season, g), finished))  # fill the cache in parallel
    logs = picks.el_logs(games, lambda g: cached_box(season, g))
    feiq = cache.get("picks:feiq", 60 * 60, picks.feiq_players, force)
    log_prices(feiq["players"])
    try:
        domestic = cache.get("picks:domestic", 6 * 3600, picks.feiq_domestic, force)
    except Exception:  # noqa: BLE001 - projections still work without domestic games
        domestic = {"games": [], "generated": None}
    try:
        inj = get_injuries(force)
    except Exception:  # noqa: BLE001
        inj = None
    injuries = {p["key"]: p for t in (inj or {}).get("teams", []) for p in t["players"]}
    return {
        "season": season, "games": games, "finished": finished, "logs": logs, "feiq": feiq,
        "domestic": domestic, "inj": inj, "injuries": injuries,
    }


PRICES_PATH = os.path.join(os.path.dirname(TRACK_DIR), "prices.jsonl")
_prices_logged = {"day": None}


def log_prices(players):
    """Append one snapshot of official prices per day. Prices move with
    performance; a season of history lets the tool learn how."""
    day = time.strftime("%Y-%m-%d")
    if _prices_logged["day"] == day:
        return
    try:
        if os.path.exists(PRICES_PATH):
            line = ""
            with open(PRICES_PATH) as f:
                for line in f:
                    pass
                if line.startswith(f'{{"day": "{day}"'):
                    _prices_logged["day"] = day
                    return
        os.makedirs(os.path.dirname(PRICES_PATH), exist_ok=True)
        snap = {"day": day, "prices": {f"{p['key']}|{p['team']}": p["price"] for p in players}}
        with open(PRICES_PATH, "a") as f:
            f.write(json.dumps(snap) + "\n")
        _prices_logged["day"] = day
    except OSError as e:
        log.warning("could not log prices: %s", e)


_team_bt_lock = threading.Lock()


def team_backtest(inp, done):
    """Team-level backtest, computed once per model version and finished
    round (it takes a while), in the background."""
    key = f"picks:teambt:v{picks.MODEL_VERSION}:{inp['season']}:{done}"
    entry = cache.data.get(key)
    if entry:
        return entry["v"]

    def run():
        if not _team_bt_lock.acquire(blocking=False):
            return
        try:
            cache.get(key, float("inf"), lambda: optimize.team_backtest(inp["feiq"]["players"], inp["logs"], inp["domestic"]["games"], inp["games"]))
        except Exception as e:  # noqa: BLE001
            log.warning("team backtest failed: %s", e)
        finally:
            _team_bt_lock.release()

    threading.Thread(target=run, daemon=True).start()
    return None


def player_budget(inp):
    """Credits available for the ten players: the saved team's value plus bank,
    or 95 (100 minus a typical coach) when no team is saved."""
    team = load_team()
    prices = {f"{p['key']}|{p['team']}": p["price"] for p in inp["feiq"]["players"]}
    if team and all(i in prices for i in team["players"]):
        return round(sum(prices[i] for i in team["players"]) + team.get("bank", 0), 1)
    return 95.0


def wildcard(inp, rows, budget):
    players = {f"{p['key']}|{p['team']}": {"pos": p["pos"], "price": p["price"]} for p in inp["feiq"]["players"] if p["pos"] in ("G", "F", "C")}
    pts = {f"{r['key']}|{r['team']}": r["xfp"] for r in rows}
    sol = optimize.best_roster(players, [(1.0, pts)], budget)
    if not sol:
        return None
    info = optimize.sim_info(rows)
    lineup = sol["lineups"][0]
    return {
        "budget": budget,
        "cost": round(sum(players[i]["price"] for i in sol["roster"]), 1),
        "value": round(sol["value"], 1),
        "lineup": lineup,
        "sim": optimize.simulate_round(sol["roster"], info, lineup),
    }


def round_rows(inputs, rnd):
    """Projections for one round, cached for 15 minutes."""
    key = f"picks:rows:v{picks.MODEL_VERSION}:{rnd}"

    def build():
        rows, ctx = picks.project(
            inputs["feiq"]["players"], inputs["logs"], inputs["domestic"]["games"], inputs["games"], rnd, time.time(), inputs["injuries"]
        )
        rows.sort(key=lambda r: -r["xfp"])
        return {"rows": rows, "home_edge": ctx["home_edge"], "rate": ctx["rate"]}

    return cache.get(key, 15 * 60, build)


def get_picks(rnd=None, force=False):
    """Projected PIR and value per credit for a EuroLeague round."""
    inp = picks_inputs(force)
    season, games, finished, logs = inp["season"], inp["games"], inp["finished"], inp["logs"]
    feiq, domestic, inj = inp["feiq"], inp["domestic"], inp["inj"]
    target = picks.next_round(games)
    rounds = sorted({g["round"] for g in games})
    rnd = int(rnd) if rnd and int(rnd) in rounds else target
    built = round_rows(inp, rnd)
    rows = built["rows"]

    done = sum(1 for r in rounds if all(g["state"] == "post" for g in games if g["round"] == r))
    bt = cache.get(
        f"picks:backtest:v{picks.MODEL_VERSION}:{season}:{done}",
        float("inf"),
        lambda: picks.backtest(feiq["players"], logs, domestic["games"], games),
    )
    info = picks._team_info(games)
    lock = picks.first_tip(games, rnd)
    try:
        wc = wildcard(inp, rows, player_budget(inp))
    except Exception as e:  # noqa: BLE001
        log.warning("wildcard failed: %s", e)
        wc = None
    lists = picks.suggestions(rows)
    if rnd == target and lock and time.time() < lock:
        try:
            picks.save_snapshot(TRACK_DIR, {"round": rnd, "players": rows, "lists": lists})
        except OSError as e:
            log.warning("could not save picks snapshot: %s", e)
    return {
        "round": rnd,
        "next_round": target,
        "rounds": [r for r in rounds if target <= r <= target + 2],
        "lock": lock,
        "players": rows,
        "lists": lists,
        "scoring": {"win_bonus": picks.WIN_BONUS, "slots": picks.SLOTS},
        "track": picks.track_record(TRACK_DIR, logs, games),
        "wildcard": wc,
        "team_backtest": team_backtest(inp, done),
        "coaches": picks.coach_rows(feiq["players"], games, rnd),
        "teams": info,
        "context": {"home_edge": round(built["home_edge"], 3), "rate": {k: round(v, 3) for k, v in built["rate"].items()}},
        "backtest": bt,
        "sources": {
            "prices": cache.fetched_at("picks:feiq"),
            "domestic": domestic.get("generated"),
            "injuries": (inj or {}).get("updated"),
            "games": len(finished),
        },
    }


TEAM_PATH = os.path.join(os.path.dirname(TRACK_DIR), "my-team.json")


def load_team():
    try:
        with open(TEAM_PATH) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_team(body):
    """Save the team as it stands in the official game. The first save in
    a new round remembers the previous team, so transfers can be counted."""
    inp = picks_inputs()
    target = picks.next_round(inp["games"])
    known = {f"{p['key']}|{p['team']}": p for p in inp["feiq"]["players"]}
    players = [i for i in body.get("players", []) if i in known]
    coach = body.get("coach") if body.get("coach") in known else None
    counts = {pos: sum(1 for i in players if known[i]["pos"] == pos) for pos in ("G", "F", "C")}
    if len(set(players)) != 10 or counts != {"G": 4, "F": 4, "C": 2} or not coach:
        raise ValueError("A team needs 4 guards, 4 forwards, 2 centers and a coach")
    old = load_team() or {}
    round_start = old.get("round_start")
    if not round_start or round_start.get("round") != target:
        base = old if old.get("players") else {"players": players, "coach": coach}
        round_start = {"round": target, "players": base["players"], "coach": base["coach"]}
    team = {
        "round": target,
        "players": players,
        "coach": coach,
        "bank": round(float(body.get("bank", 0)), 1),
        "lineup": body.get("lineup"),
        "unlimited": bool(body.get("unlimited")),
        "round_start": round_start,
        "live": old.get("live"),
        "saved_at": time.time(),
    }
    os.makedirs(os.path.dirname(TEAM_PATH), exist_ok=True)
    tmp = TEAM_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(team, f, indent=1)
    os.replace(tmp, TEAM_PATH)
    return team


def live_box(season, game):
    """Box score for a game in progress, refreshed every minute."""
    return cache.get(f"boxlive:{season}:{game['id']}", 60, lambda: fantasy.box_score(season, game))


def get_live_team():
    """The saved lineup for a round in progress, scored game by game."""
    team = load_team()
    live = (team or {}).get("live")
    if not live:
        return {"live": None}
    inp = picks_inputs()
    rnd = live["round"]
    lineup = live["lineup"]
    games = sports.el_games(inp["season"]) if any(g["round"] == rnd and g["state"] == "in" for g in inp["games"]) else inp["games"]
    fixtures = picks._round_games(games, rnd)
    proj = {f"{r['key']}|{r['team']}": r for r in round_rows(inp, rnd)["rows"]}
    people = {f"{p['key']}|{p['team']}": p for p in inp["feiq"]["players"]}

    def role(i):
        if i == lineup["captain"]:
            return "captain"
        if i in lineup["starters"]:
            return "starter"
        return "sixth" if i == lineup["sixth"] else "bench"

    mult = {"captain": 2.0, "starter": 1.0, "sixth": 1.0, "bench": 0.5}
    rows, entries = [], {}
    for i in lineup["starters"] + [lineup["sixth"]] + lineup["bench"]:
        p = people.get(i, {})
        key, team_code = i.rsplit("|", 1)[0], i.rsplit("|", 1)[1]
        g, home = fixtures.get(team_code, (None, None))
        state = g["state"] if g else "none"
        line = None
        if state in ("post", "in"):
            box = cached_box(inp["season"], g) if state == "post" else live_box(inp["season"], g)
            line = next((x for x in box if x["key"] == key and x["team"] == team_code), None)
        won = None
        if state == "post":
            won = (g.get("winner") == "home") == bool(home)
        pir = line["pir"] if line else (0 if state == "post" else None)
        fp = pir * (1 + picks.WIN_BONUS * bool(won)) if pir is not None else None
        r = role(i)
        expected = proj.get(i, {}).get("xfp", 0.0)
        value = fp if state in ("post", "in") else expected
        entries[i] = {"value": value or 0.0, "locked": state in ("post", "in"), "tip": g["ts"] if g else None}
        opp = (g["away"] if home else g["home"]) if g else None
        rows.append(
            {
                "id": i,
                "name": p.get("name", key),
                "team": team_code,
                "pos": p.get("pos"),
                "price": p.get("price"),
                "role": r,
                "mult": mult[r],
                "state": state,
                "tip": g["ts"] if g else None,
                "opp": opp["code"] if opp else None,
                "home": home,
                "score": [g["home"]["score"], g["away"]["score"]] if g and state != "pre" else None,
                "detail": g.get("detail") if g else None,
                "won": won,
                "played": line is not None,
                "min": line["min"] if line else None,
                "pir": pir,
                "pts": line["pts"] if line else None,
                "reb": line["reb"] if line else None,
                "ast": line["ast"] if line else None,
                "fp": round(fp, 1) if fp is not None else None,
                "xfp": expected,
                "status": proj.get(i, {}).get("status"),
                "severity": proj.get(i, {}).get("severity"),
                "total": round((fp if fp is not None else 0) * mult[r], 1),
            }
        )
    banked = sum(r["total"] for r in rows if r["state"] == "post")
    live_now = sum(r["total"] for r in rows if r["state"] == "in")
    to_come = sum(r["xfp"] * r["mult"] for r in rows if r["state"] == "pre")
    coach = None
    if team.get("coach"):
        c_team = team["coach"].rsplit("|", 1)[1]
        g, home = fixtures.get(c_team, (None, None))
        cp = people.get(team["coach"], {})
        coach = {
            "name": cp.get("name"),
            "team": c_team,
            "state": g["state"] if g else None,
            "tip": g["ts"] if g else None,
            "opp": ((g["away"] if home else g["home"])["code"]) if g else None,
            "home": home,
            "won": ((g.get("winner") == "home") == bool(home)) if g and g["state"] == "post" else None,
            "score": [g["home"]["score"], g["away"]["score"]] if g and g["state"] != "pre" else None,
        }
    subs = picks.gameday_subs(lineup, entries)
    next_tip = min((r["tip"] for r in rows if r["state"] == "pre" and r["tip"]), default=None)
    return {
        "live": {
            "round": rnd,
            "lineup": lineup,
            "players": rows,
            "coach": coach,
            "banked": round(banked, 1),
            "live_now": round(live_now, 1),
            "to_come": round(to_come, 1),
            "projected": round(banked + live_now + to_come, 1),
            "subs": subs,
            "next_tip": next_tip,
            "done": all(r["state"] == "post" for r in rows),
        }
    }


def save_live_lineup(body):
    team = load_team()
    if not team or not team.get("live"):
        raise ValueError("No live lineup saved")
    l = body.get("lineup") or {}
    ids = list(l.get("starters", [])) + [l.get("sixth")] + list(l.get("bench", []))
    if sorted(ids) != sorted(team["players"]) or l.get("captain") not in l.get("starters", []):
        raise ValueError("The lineup must use your ten players with the captain among the starters")
    team["live"]["lineup"] = {"captain": l["captain"], "starters": l["starters"], "sixth": l["sixth"], "bench": l["bench"]}
    tmp = TEAM_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(team, f, indent=1)
    os.replace(tmp, TEAM_PATH)
    return get_live_team()


def suggest_transfers(body):
    """Best transfers for a draft roster: exact optimisation for each number
    of transfers, re-ranked by a simulation of the round with daily subs."""
    inp = picks_inputs()
    target = picks.next_round(inp["games"])
    rnd = int(body.get("round") or target)
    rows = round_rows(inp, rnd)["rows"]
    pts = {f"{r['key']}|{r['team']}": r["xfp"] for r in rows}
    info = optimize.sim_info(rows)
    players = {
        f"{p['key']}|{p['team']}": {"pos": p["pos"], "price": p["price"]}
        for p in inp["feiq"]["players"]
        if p["pos"] in ("G", "F", "C")
    }
    roster = [i for i in body.get("players", []) if i in players]
    if len(roster) != 10:
        raise ValueError("Pick all ten players first")
    coach_price = next((p["price"] for p in inp["feiq"]["players"] if f"{p['key']}|{p['team']}" == body.get("coach")), 0.0)
    budget = float(body.get("budget", 0)) - coach_price
    max_moves = max(0, min(int(body.get("max_moves", 4)), 10))

    for i in players:  # players without a game this round score nothing
        info.setdefault(i, {"mean": 0.0, "sd": 1.0, "p": 0.0, "win": 0.5, "team": i, "tip": None})

    def simulate(ros, lineup=None):
        return optimize.simulate_round(ros, info, lineup)

    base_value = picks.lineup_value([pts.get(i, 0.0) for i in roster])
    current = {"value": round(base_value, 1), "sim": simulate(roster)}
    options, seen = [], set()
    counts = list(range(1, min(max_moves, 4) + 1))
    if max_moves > 4:
        counts.append(max_moves)  # a full rebuild when transfers are unlimited
    for k in counts:
        cands = optimize.k_best_rosters(players, [(1.0, pts)], budget, roster, k, k=3)
        best = None
        for sol in cands:
            sim = simulate(sol["roster"], sol["lineups"][0])
            if best is None or sim["mean"] > best[1]["mean"]:
                best = (sol, sim)
        if not best:
            continue
        sol, sim = best
        key = frozenset(sol["roster"])
        if key in seen or sol["value"] <= base_value + 0.05:
            continue
        seen.add(key)
        sells = sorted((i for i in roster if i not in key), key=lambda i: players[i]["pos"])
        buys = sorted((i for i in sol["roster"] if i not in roster), key=lambda i: players[i]["pos"])
        # pair sells and buys by position for display
        moves = []
        for pos in ("G", "F", "C"):
            o = [i for i in sells if players[i]["pos"] == pos]
            n = [i for i in buys if players[i]["pos"] == pos]
            moves += [list(m) for m in zip(o, n)]
        cost = sum(players[i]["price"] for i in sol["roster"])
        options.append(
            {
                "transfers": len(moves),
                "moves": moves,
                "gain": round(sol["value"] - base_value, 1),
                "sim_gain": round(sim["mean"] - current["sim"]["mean"], 1),
                "sim": sim,
                "lineup": sol["lineups"][0],
                "cost": round(cost, 1),
                "bank": round(budget - cost, 1),
                "rebuild": k > 4,
            }
        )
    return {"current": current, "options": options}


def get_meta():
    cfg = config()
    return {"name": cfg.get("name", ""), "favorite_teams": cfg.get("favorite_teams", [])}


def keep_picks_fresh():
    """Recompute picks every 30 minutes so the saved pre-lock snapshot is
    always close to the real lineup lock."""
    while True:
        time.sleep(30 * 60)
        _quiet(get_picks)


def warm_up():
    """Fill the cache in the background right after start-up."""
    jobs = [lambda lg=lg: get_league(lg) for lg in LEAGUES]
    jobs += [get_fantasy, get_picks]
    t0 = time.time()
    threads = [threading.Thread(target=_quiet, args=(j,), daemon=True) for j in jobs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    log.info("warm-up finished in %.1fs", time.time() - t0)


def _quiet(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        log.warning("warm-up: %s", e)


# ---------------------------------------------------------------- http


class Handler(BaseHTTPRequestHandler):
    server_version = "FantasyDesk/1.0"

    def log_message(self, fmt, *args):  # keep the log readable
        if os.environ.get("WORLD_NEWS_DEBUG"):
            super().log_message(fmt, *args)

    def do_GET(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        force = q.get("fresh", ["0"])[0] == "1"
        parts = [p for p in url.path.split("/") if p]
        try:
            if not parts:
                return self._file(os.path.join(STATIC, "index.html"))
            if parts[0] == "static" and len(parts) > 1:
                path = os.path.realpath(os.path.join(STATIC, *parts[1:]))
                if not path.startswith(STATIC + os.sep):
                    return self._error(404, "Not found")
                return self._file(path)
            if parts[0] == "api":
                return self._api(parts[1:], force)
            return self._error(404, "Not found")
        except BrokenPipeError:
            pass
        except Exception as e:  # noqa: BLE001
            log.exception("request failed")
            self._error(502, f"Could not load data: {e}")

    def _api(self, parts, force):
        route = parts[0] if parts else ""
        arg = parts[1] if len(parts) > 1 else None
        if route == "health":
            return self._json({"ok": True})
        if route == "meta":
            return self._json(get_meta())
        if route == "sports":
            data = get_league(arg, force)
        elif route == "fantasy":
            data = get_fantasy(force)
        elif route == "picks":
            data = get_picks(arg, force)
        elif route == "myteam" and arg == "live":
            data = get_live_team()
        elif route == "myteam":
            data = {"team": load_team()}
        else:
            data = None
        if data is None:
            return self._error(404, "Unknown endpoint")
        return self._json(data)

    def do_POST(self):
        parts = [p for p in urlparse(self.path).path.split("/") if p]
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > 200_000:
                return self._error(413, "Request too large")
            body = json.loads(self.rfile.read(length) or b"{}")
            if parts == ["api", "myteam"]:
                return self._json({"team": save_team(body)})
            if parts == ["api", "myteam", "live"]:
                return self._json(save_live_lineup(body))
            if parts == ["api", "myteam", "suggest"]:
                return self._json(suggest_transfers(body))
            return self._error(404, "Unknown endpoint")
        except ValueError as e:
            return self._error(400, str(e))
        except Exception as e:  # noqa: BLE001
            log.exception("POST failed")
            return self._error(502, f"Could not complete the request: {e}")

    def _json(self, obj, status=200):
        body = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, message):
        self._json({"error": message}, status)

    def _file(self, path):
        if not os.path.isfile(path):
            return self._error(404, "Not found")
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "image/svg+xml"):
            ctype += "; charset=utf-8"
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--no-warmup", action="store_true")
    args = ap.parse_args()
    port = args.port or int(config().get("port", 8420))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.daemon_threads = True
    log.info("Fantasy Desk on http://localhost:%d", port)
    if not args.no_warmup:
        threading.Thread(target=warm_up, daemon=True).start()
        threading.Thread(target=keep_picks_fresh, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        cache._save()


if __name__ == "__main__":
    main()
