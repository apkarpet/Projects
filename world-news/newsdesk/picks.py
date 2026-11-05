"""EuroLeague Fantasy Challenge pick suggestions.

For every player this projects PIR in his team's game in a target round and
divides it by his price in credits. Every number comes with the reasons behind
it, and the same model is replayed on finished rounds (backtest) so its
accuracy can be judged against simple baselines.

Projection = projected minutes x PIR-per-minute x matchup x home/away x availability

- Minutes: recency-weighted EuroLeague minutes, nudged by recent domestic
  minutes, plus minutes inherited from teammates who just went out injured.
- PIR per minute: last season's rate as a prior, updated with this season's
  EuroLeague minutes (recent games count extra) and domestic games (count less).
- Matchup: how much PIR the opponent allows to the player's position, shrunk
  towards league average while samples are small.
- Home/away: the league-wide home edge, measured from this season's games.
- Availability: BasketNews injury status.
"""

import csv
import io
import json
import math
import statistics
import time
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from .fantasy import player_key
from .net import fetch_text

FEIQ = "https://www.fantasyedgeiq.com"
CET = ZoneInfo("Europe/Paris")

PRIOR_MINUTES = 80  # how strongly last season's rate anchors this season's
RECENT_EXTRA = 0.5  # extra weight on the last 3 EuroLeague games
DOMESTIC_WEIGHT = 0.3  # domestic minutes count 30% as much as EuroLeague ones
DOMESTIC_EST_WEIGHT = 0.2  # ...and less when PIR had to be estimated
AVAILABILITY = {0: 0.0, 1: 0.4, 2: 0.75, 3: 0.95}  # by injury severity
MAX_INHERITED = 6.0  # cap on minutes a player can inherit from injured teammates


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- sources


def feiq_players():
    """Official-game prices, popularity and positions (FantasyEdgeIQ CSV)."""
    text = fetch_text(f"{FEIQ}/euroleague-players-full.csv", timeout=25)
    out, seen = [], set()
    for r in csv.DictReader(io.StringIO(text)):
        if not r.get("name") or _f(r.get("price")) is None:
            continue
        ident = (player_key(r["name"]), r["team_abbr"], r["pos_short"])
        if ident in seen:  # the CSV occasionally lists a player twice
            continue
        seen.add(ident)
        out.append(
            {
                "name": r["name"],
                "key": player_key(r["name"]),
                "team": r["team_abbr"],
                "pos": r["pos_short"],
                "price": _f(r["price"]),
                "price_change": _f(r.get("price_change")) or 0.0,
                "popularity": _f(r.get("popularity_pct")) or 0.0,
                "injured_flag": r.get("is_injured") == "True",
                "bench": r.get("started_from_bench") == "True",
                "feiq_proj": _f(r.get("proj_pir_est")),
                "pir_prev": _f(r.get("pir_25_26")),
                "min_prev": _f(r.get("min_avg_25_26")),
                "team_fga": _f(r.get("team_fga_for_pg")),
            }
        )
    return {"players": out, "fetched": time.time()}


def feiq_domestic():
    """Domestic league/cup box scores for EuroLeague clubs (FantasyEdgeIQ)."""
    page = fetch_text(f"{FEIQ}/euroleague/domestic-competitions", timeout=40)
    start = page.index("const DATA=") + len("const DATA=")
    data = json.JSONDecoder().raw_decode(page[start:])[0]
    games = []
    for p in data.get("players", []):
        if p.get("is_total") or p.get("is_team_bench") or p.get("status") != "played":
            continue
        mins = _f(p.get("minutes"))
        if not mins:
            continue
        try:
            ts = datetime.strptime(p["date_local"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=CET).timestamp()
        except (KeyError, ValueError):
            continue
        games.append(
            {
                "key": player_key(p["player"]),
                "team": p.get("team_abbr"),
                "ts": ts,
                "league": p.get("league"),
                "opp": p.get("opponent_abbr") or p.get("opponent_name"),
                "min": round(mins, 1),
                "pir": _f(p.get("rank")) or 0.0,
                "pts": _f(p.get("pts")) or 0.0,
                "est": "est" in (p.get("source_quality") or ""),
            }
        )
    return {"generated": data.get("generated"), "games": games}


# ---------------------------------------------------------------- inputs


def el_logs(games, box):
    """Flatten finished EuroLeague games into one row per player per game."""
    logs = []
    for g in games:
        if g["state"] != "post":
            continue
        for line in box(g):
            home = line["team"] == g["home"]["code"]
            logs.append(
                {
                    **line,
                    "round": g["round"],
                    "ts": g["ts"],
                    "game": g["id"],
                    "home": home,
                    "opp": g["away"]["code"] if home else g["home"]["code"],
                    "min": line.get("secs", line["min"] * 60) / 60,
                }
            )
    logs.sort(key=lambda r: r["ts"])
    return logs


def _team_info(games):
    info = {}
    for g in games:
        for side in ("home", "away"):
            t = g[side]
            info.setdefault(t["code"], {"name": t["name"], "crest": t.get("crest")})
    return info


def _round_games(games, rnd):
    by_team = {}
    for g in games:
        if g["round"] == rnd:
            by_team[g["home"]["code"]] = (g, True)
            by_team[g["away"]["code"]] = (g, False)
    return by_team


def next_round(games, now=None):
    """The first round that has not tipped off yet (lineups lock at tip-off)."""
    now = now or time.time()
    firsts = defaultdict(lambda: float("inf"))
    for g in games:
        firsts[g["round"]] = min(firsts[g["round"]], g["ts"])
    upcoming = [r for r, t in firsts.items() if t > now]
    return min(upcoming) if upcoming else max(firsts)


def first_tip(games, rnd):
    return min((g["ts"] for g in games if g["round"] == rnd), default=None)


# ---------------------------------------------------------------- model


def _league_context(logs, posmap):
    """League PIR/min by position, home edge and PIR allowed by position."""
    mins, pir = defaultdict(float), defaultdict(float)
    home = {True: [0.0, 0.0], False: [0.0, 0.0]}
    allowed = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # team -> pos -> game -> pir
    for r in logs:
        pos = posmap.get(r["key"]) or r.get("pos") or "F"
        mins[pos] += r["min"]
        pir[pos] += r["pir"]
        home[r["home"]][0] += r["pir"]
        home[r["home"]][1] += r["min"]
        allowed[r["opp"]][pos][r["game"]] += r["pir"]
    rate = {p: pir[p] / mins[p] for p in mins if mins[p]}
    overall = sum(pir.values()) / max(1, sum(mins.values()))
    for p in ("G", "F", "C"):
        rate.setdefault(p, overall or 0.6)
    h = home[True][0] / max(1, home[True][1])
    a = home[False][0] / max(1, home[False][1])
    edge = math.sqrt(h / a) if h and a else 1.0

    dvp = {}
    league_avg = {}
    for p in ("G", "F", "C"):
        vals = [statistics.mean(allowed[t][p].values()) for t in allowed if allowed[t][p]]
        league_avg[p] = statistics.mean(vals) if vals else 0
    for t in allowed:
        dvp[t] = {}
        for p in ("G", "F", "C"):
            games = allowed[t][p]
            if not games or not league_avg[p]:
                dvp[t][p] = (1.0, 0)
                continue
            ratio = statistics.mean(games.values()) / league_avg[p]
            shrink = len(games) / (len(games) + 4)
            dvp[t][p] = (max(0.85, min(1.15, 1 + 0.7 * (ratio - 1) * shrink)), len(games))
    # rank 1 = most generous defence for that position
    ranks = {}
    for p in ("G", "F", "C"):
        order = sorted(dvp, key=lambda t: -dvp[t][p][0])
        for i, t in enumerate(order, 1):
            ranks[(t, p)] = i
    return {"rate": rate, "home_edge": edge, "dvp": dvp, "dvp_rank": ranks, "teams": len(dvp)}


def _ewma(values, alpha=0.4):
    if not values:
        return None
    w, tot, acc = 1.0, 0.0, 0.0
    for v in reversed(values):
        acc += w * v
        tot += w
        w *= 1 - alpha
    return acc / tot


def project(players, logs, domestic, games, rnd, cutoff, injuries=None):
    """Project every priced player for round `rnd`, using only data before
    `cutoff` (a timestamp). Returns (rows, context)."""
    logs = [r for r in logs if r["ts"] < cutoff]
    dom = [d for d in domestic if d["ts"] < cutoff]
    posmap = {p["key"]: p["pos"] for p in players if p["pos"] in ("G", "F", "C")}
    ctx = _league_context(logs, posmap)
    fixtures = _round_games(games, rnd)
    injuries = injuries or {}

    by_key = defaultdict(list)
    for r in logs:
        by_key[r["key"]].append(r)
    dom_by_key = defaultdict(list)
    for d in dom:
        dom_by_key[d["key"]].append(d)
    team_ts = defaultdict(set)
    for r in logs:
        team_ts[r["team"]].add(r["ts"])
    team_games = {t: sorted(v) for t, v in team_ts.items()}

    rows = []
    for p in players:
        if p["pos"] not in ("G", "F", "C"):
            continue
        fx = fixtures.get(p["team"])
        if not fx:
            continue
        game, is_home = fx
        opp = game["away"] if is_home else game["home"]
        el = [r for r in by_key.get(p["key"], []) if r["team"] == p["team"]] or by_key.get(p["key"], [])
        dm = [d for d in dom_by_key.get(p["key"], []) if d["team"] == p["team"]]
        recent_dom = [d for d in dm if cutoff - d["ts"] < 21 * 86400][-3:]
        reasons = []

        # --- minutes
        n = len(el)
        el_min = [r["min"] for r in el]
        m_el = _ewma(el_min)
        missed = 0
        if el:
            missed = sum(1 for t in team_games.get(p["team"], []) if t > el[-1]["ts"])
        team_played = len(team_games.get(p["team"], []))
        if n:
            minutes = m_el
            if recent_dom:
                m_dom = statistics.mean(d["min"] for d in recent_dom)
                minutes = 0.8 * minutes + 0.2 * m_dom
            if missed >= 2:
                minutes *= 0.5
                reasons.append(f"Has sat out the last {missed} EuroLeague games")
            elif missed == 1:
                minutes *= 0.85
                reasons.append("Missed his team's last EuroLeague game")
        elif recent_dom:
            minutes = 0.85 * statistics.mean(d["min"] for d in recent_dom)
            reasons.append("No EuroLeague minutes yet, projected from domestic games")
        elif p["min_prev"] and team_played < 3:
            minutes = 0.8 * p["min_prev"]
        else:
            minutes = 4.0 if team_played >= 3 else 8.0

        # --- PIR per minute
        prior = (
            p["pir_prev"] / p["min_prev"]
            if p["pir_prev"] is not None and p["min_prev"] and p["min_prev"] >= 8
            else ctx["rate"][p["pos"]]
        )
        num, den = prior * PRIOR_MINUTES, PRIOR_MINUTES
        for r in el:
            num += r["pir"]
            den += r["min"]
        for r in el[-3:]:
            num += RECENT_EXTRA * r["pir"]
            den += RECENT_EXTRA * r["min"]
        for d in dm[-5:]:
            w = DOMESTIC_EST_WEIGHT if d["est"] else DOMESTIC_WEIGHT
            num += w * d["pir"]
            den += w * d["min"]
        rate = num / den if den else prior

        # --- matchup and venue
        dvp, dvp_games = ctx["dvp"].get(opp["code"], {}).get(p["pos"], (1.0, 0))
        venue = ctx["home_edge"] if is_home else 1 / ctx["home_edge"]

        # --- availability
        inj = injuries.get(p["key"])
        avail = 1.0
        if inj:
            avail = AVAILABILITY.get(inj["severity"], 0.75)
        elif p["injured_flag"]:
            avail = 0.5
            reasons.append("Flagged injured in the fantasy game")

        rows.append(
            {
                "p": p,
                "game": game,
                "home": is_home,
                "opp": opp,
                "el": el,
                "dom": dm,
                "minutes": minutes,
                "rate": rate,
                "prior": prior,
                "dvp": dvp,
                "dvp_games": dvp_games,
                "venue": venue,
                "avail": avail,
                "inj": inj,
                "missed": missed,
                "reasons": reasons,
                "vacated": [],
            }
        )

    # --- minutes left behind by teammates who just went out
    by_team = defaultdict(list)
    for r in rows:
        by_team[r["p"]["team"]].append(r)
    for team, members in by_team.items():
        last_game = team_games.get(team, [None])[-1] if team_games.get(team) else None
        newly_out = [
            r for r in members
            if r["avail"] <= 0.4 and r["el"] and last_game is not None and r["el"][-1]["ts"] >= last_game
        ]
        if not newly_out:
            continue
        healthy = [r for r in members if r["avail"] > 0.4 and r["minutes"] >= 6]
        for gone in newly_out:
            freed = gone["minutes"] * (1 - gone["avail"])
            same = [r for r in healthy if r["p"]["pos"] == gone["p"]["pos"]]
            pools = ((same, 0.55), (healthy, 0.2))
            for pool, share in pools:
                tot = sum(r["minutes"] for r in pool)
                if not tot:
                    continue
                for r in pool:
                    room = MAX_INHERITED - sum(x for _, x in r["vacated"])
                    extra = min(freed * share * r["minutes"] / tot, max(0.0, room))
                    r["minutes"] += extra
                    r["vacated"].append((gone["p"]["name"], extra))

    out = []
    for r in rows:
        p = r["p"]
        minutes = min(r["minutes"], 34.0)
        proj = minutes * r["rate"] * r["dvp"] * r["venue"] * r["avail"]
        el = r["el"]
        pirs = [x["pir"] for x in el]
        season = statistics.mean(pirs) if pirs else None
        sd = statistics.pstdev(pirs) if len(pirs) >= 3 else 0.45 * max(proj, 4)
        if season and season > 0:
            sd *= max(0.5, min(1.5, proj / season))
        l3 = statistics.mean(pirs[-3:]) if pirs else None
        dom_l3 = r["dom"][-3:]
        fga = sum(x["fga"] for x in el)
        mins_el = sum(x["min"] for x in el)
        # share of the team's shots taken while he is on the floor
        usage = (fga / mins_el * 40) / p["team_fga"] * 100 if p["team_fga"] and mins_el else None

        reasons = list(r["reasons"])
        gained = sum(x for _, x in r["vacated"])
        if gained >= 0.8:
            names = ", ".join(sorted({n for n, _ in r["vacated"]}))
            names = ", ".join(sorted({n for n, x in r["vacated"] if x > 0.1}))
            reasons.append(f"+{gained:.1f} min with {names} out")
        if r["dvp"] >= 1.04:
            reasons.append(f"{r['opp']['name']} give up {round((r['dvp'] - 1) * 100)}% more PIR than average to {POS_WORD[p['pos']]}")
        elif r["dvp"] <= 0.96:
            reasons.append(f"{r['opp']['name']} allow {round((1 - r['dvp']) * 100)}% less PIR than average to {POS_WORD[p['pos']]}")
        if l3 is not None and season and len(pirs) >= 5:
            if l3 >= season + 4:
                reasons.append(f"Hot: {l3:.1f} PIR over the last 3 vs {season:.1f} on the season")
            elif l3 <= season - 4:
                reasons.append(f"Cold: {l3:.1f} PIR over the last 3 vs {season:.1f} on the season")
        if r["inj"]:
            reasons.insert(0, f"{r['inj']['status']}: {r['inj']['comment']}")
        if dom_l3 and len(dom_l3) >= 2:
            dpir = statistics.mean(d["pir"] for d in dom_l3)
            if season is not None and dpir >= season + 5:
                reasons.append(f"Strong in the domestic league lately ({dpir:.1f} PIR)")

        price = p["price"] or 0
        out.append(
            {
                "name": p["name"],
                "key": p["key"],
                "team": p["team"],
                "pos": p["pos"],
                "price": price,
                "price_change": p["price_change"],
                "popularity": p["popularity"],
                "opp": r["opp"]["code"],
                "opp_name": r["opp"]["name"],
                "opp_crest": r["opp"].get("crest"),
                "home": r["home"],
                "tip": r["game"]["ts"],
                "proj": round(proj, 1),
                "floor": round(max(0.0, proj - sd), 1),
                "ceil": round(proj + sd, 1),
                "value": round(proj / price, 2) if price else None,
                "minutes": round(minutes * r["avail"], 1),
                "rate": round(r["rate"], 3),
                "season": round(season, 1) if season is not None else None,
                "l3": round(l3, 1) if l3 is not None else None,
                "gp": len(pirs),
                "min_avg": round(mins_el / len(el), 1) if el else None,
                "dom_l3": round(statistics.mean(d["pir"] for d in dom_l3), 1) if dom_l3 else None,
                "dom_min": round(statistics.mean(d["min"] for d in dom_l3), 1) if dom_l3 else None,
                "dom_est": any(d["est"] for d in dom_l3),
                "usage": round(usage, 1) if usage else None,
                "fta40": round(sum(x["fta"] for x in el) / mins_el * 40, 1) if mins_el else None,
                "starts": sum(1 for x in el if x.get("start")),
                "dvp": round(r["dvp"], 3),
                "dvp_rank": ctx["dvp_rank"].get((r["opp"]["code"], p["pos"])),
                "venue": round(r["venue"], 3),
                "status": r["inj"]["status"] if r["inj"] else ("Injured" if p["injured_flag"] else None),
                "severity": r["inj"]["severity"] if r["inj"] else (2 if p["injured_flag"] else None),
                "feiq_proj": p["feiq_proj"],
                "reasons": reasons,
                "games": [
                    {"ts": x["ts"], "pir": x["pir"], "min": round(x["min"]), "opp": x["opp"], "comp": "EL"} for x in el[-8:]
                ]
                + [
                    {"ts": d["ts"], "pir": d["pir"], "min": round(d["min"]), "opp": d["opp"], "comp": d["league"], "est": d["est"]}
                    for d in r["dom"][-6:]
                ],
            }
        )
    for o in out:
        o["games"].sort(key=lambda g: g["ts"])
        o["games"] = o["games"][-10:]
    return out, ctx


POS_WORD = {"G": "guards", "F": "forwards", "C": "centers"}


# ---------------------------------------------------------------- coaches


def coach_rows(players, games, rnd):
    """Coaches score on results, so rank them by win chance from net rating."""
    net = defaultdict(lambda: [0.0, 0])
    for g in games:
        if g["state"] != "post":
            continue
        d = g["home"]["score"] - g["away"]["score"]
        net[g["home"]["code"]][0] += d
        net[g["home"]["code"]][1] += 1
        net[g["away"]["code"]][0] -= d
        net[g["away"]["code"]][1] += 1

    def rating(t):
        tot, n = net[t]
        return (tot / n) * n / (n + 3) if n else 0.0

    fixtures = _round_games(games, rnd)
    out = []
    for p in players:
        if p["pos"] != "HC" or p["team"] not in fixtures:
            continue
        g, home = fixtures[p["team"]]
        opp = g["away"] if home else g["home"]
        spread = rating(p["team"]) - rating(opp["code"]) + (3.0 if home else -3.0)
        win = 0.5 * (1 + math.erf(spread / (11 * math.sqrt(2))))
        out.append(
            {
                "name": p["name"],
                "team": p["team"],
                "price": p["price"],
                "popularity": p["popularity"],
                "opp": opp["code"],
                "home": home,
                "win": round(win * 100),
                "spread": round(spread, 1),
            }
        )
    out.sort(key=lambda c: -c["win"])
    return out


# ---------------------------------------------------------------- lists


def suggestions(rows):
    able = [r for r in rows if (r["severity"] is None or r["severity"] >= 2) and r["proj"] > 0]
    by_proj = sorted(able, key=lambda r: -r["proj"])
    values = sorted((r["value"] for r in able if r["value"] and r["proj"] >= 6), reverse=True)
    median_value = statistics.median(values) if values else 1.0
    pick = lambda rs, n=10: [r["key"] + "|" + r["team"] for r in rs[:n]]
    return {
        "top": pick(by_proj),
        "value": pick(sorted([r for r in able if r["proj"] >= 9], key=lambda r: -(r["value"] or 0))),
        "differentials": pick([r for r in by_proj if r["popularity"] < 8 and r["proj"] >= 12]),
        "fades": pick(
            sorted(
                [
                    r for r in rows
                    if r["popularity"] >= 10
                    and ((r["severity"] is not None and r["severity"] <= 1) or (r["value"] or 0) < 0.85 * median_value)
                ],
                key=lambda r: -r["popularity"],
            ),
            8,
        ),
        "median_value": round(median_value, 2),
    }


# ---------------------------------------------------------------- backtest


def backtest(players, logs, domestic, games, min_round=4):
    """Replay the model on finished rounds using only earlier data, and
    compare it to two simple baselines: season average and last-3 average."""
    rounds = sorted({g["round"] for g in games if g["state"] == "post"})
    done = [r for r in rounds if all(g["state"] == "post" for g in games if g["round"] == r)]
    results = []
    for rnd in done:
        if rnd < min_round:
            continue
        cutoff = first_tip(games, rnd)
        rows, _ = project(players, logs, domestic, games, rnd, cutoff)
        actual = {(r["key"], r["team"]): r["pir"] for r in logs if r["round"] == rnd}
        pairs = []
        for r in rows:
            a = actual.get((r["key"], r["team"]))
            if a is None or r["season"] is None:
                continue
            pairs.append((r["proj"], r["season"], r["l3"], a))
        if len(pairs) < 30:
            continue

        def mae(i):
            return statistics.mean(abs(x[i] - x[3]) for x in pairs)

        def corr(i):
            xs, ys = [x[i] for x in pairs], [x[3] for x in pairs]
            try:
                return statistics.correlation(xs, ys)
            except statistics.StatisticsError:
                return 0.0

        def top_actual(i, n=20):
            best = sorted(pairs, key=lambda x: -x[i])[:n]
            return statistics.mean(x[3] for x in best)

        results.append(
            {
                "round": rnd,
                "players": len(pairs),
                "model": {"mae": round(mae(0), 2), "corr": round(corr(0), 3), "top20": round(top_actual(0), 1)},
                "season": {"mae": round(mae(1), 2), "corr": round(corr(1), 3), "top20": round(top_actual(1), 1)},
                "last3": {"mae": round(mae(2), 2), "corr": round(corr(2), 3), "top20": round(top_actual(2), 1)},
            }
        )
    summary = {}
    if results:
        for k in ("model", "season", "last3"):
            summary[k] = {
                m: round(statistics.mean(r[k][m] for r in results), 3 if m == "corr" else 2) for m in ("mae", "corr", "top20")
            }
    return {"rounds": results, "summary": summary}
