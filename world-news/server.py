#!/usr/bin/env python3
"""World News: a personal morning news site served on localhost.

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

from newsdesk import fantasy, feeds, markets, picks, sports
from newsdesk.cache import Cache

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
CONFIG_PATH = os.path.join(ROOT, "config.json")
CACHE_DIR = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "world-news")

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

NEWS_TTL = 15 * 60
LEAGUES = {"euroleague": sports.euroleague, "nba": sports.nba, "gbl": sports.gbl}


def sports_ttl(payload):
    return 60 if sports.has_live(payload) else 10 * 60


def get_news(section, force=False):
    cfg = config()
    sec = cfg["sections"].get(section)
    if sec is None:
        return None
    key = f"news:{section}:{_digest([sec, cfg.get('source_lists'), cfg.get('exclude_titles')])}"
    data = cache.get(key, NEWS_TTL, lambda: feeds.build_section(
            sec, cfg.get("max_age_hours", 72), cfg.get("source_lists"), cfg.get("exclude_titles")
        ), force)
    return {**data, "fetched": cache.fetched_at(key)}


def get_league(league, force=False):
    fn = LEAGUES.get(league)
    if fn is None:
        return None
    key = f"sports:{league}"
    data = cache.get(key, sports_ttl, fn, force)
    return {**data, "fetched": cache.fetched_at(key)}


def cached_box(season, game):
    return cache.get(f"box2:{season}:{game['id']}", float("inf"), lambda: fantasy.box_score(season, game))


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


def get_picks(rnd=None, force=False):
    """Projected PIR and value per credit for a EuroLeague round."""
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
    try:
        domestic = cache.get("picks:domestic", 6 * 3600, picks.feiq_domestic, force)
    except Exception:  # noqa: BLE001 - projections still work without domestic games
        domestic = {"games": [], "generated": None}
    try:
        inj = get_injuries(force)
    except Exception:  # noqa: BLE001
        inj = None
    injuries = {p["key"]: p for t in (inj or {}).get("teams", []) for p in t["players"]}

    target = picks.next_round(games)
    rounds = sorted({g["round"] for g in games})
    rnd = int(rnd) if rnd and int(rnd) in rounds else target
    rows, ctx = picks.project(feiq["players"], logs, domestic["games"], games, rnd, time.time(), injuries)
    rows.sort(key=lambda r: -r["proj"])

    done = sum(1 for r in rounds if all(g["state"] == "post" for g in games if g["round"] == r))
    bt = cache.get(
        f"picks:backtest:{season}:{done}",
        float("inf"),
        lambda: picks.backtest(feiq["players"], logs, domestic["games"], games),
    )
    info = picks._team_info(games)
    return {
        "round": rnd,
        "next_round": target,
        "rounds": [r for r in rounds if target <= r <= target + 2],
        "lock": picks.first_tip(games, rnd),
        "players": rows,
        "lists": picks.suggestions(rows),
        "coaches": picks.coach_rows(feiq["players"], games, rnd),
        "teams": info,
        "context": {"home_edge": round(ctx["home_edge"], 3), "rate": {k: round(v, 3) for k, v in ctx["rate"].items()}},
        "backtest": bt,
        "sources": {
            "prices": cache.fetched_at("picks:feiq"),
            "domestic": domestic.get("generated"),
            "injuries": (inj or {}).get("updated"),
            "games": len(finished),
        },
    }


def get_markets(force=False):
    cfg = config()
    key = f"markets:{_digest(cfg.get('markets', []))}"
    try:
        data = cache.get(key, 5 * 60, lambda: markets.quotes(cfg.get("markets", [])), force)
    except Exception:  # noqa: BLE001
        data = []
    return {"quotes": data, "fetched": cache.fetched_at(key)}


def get_meta():
    cfg = config()
    return {
        "name": cfg.get("name", ""),
        "favorite_teams": cfg.get("favorite_teams", []),
        "sections": [
            {
                "id": sid,
                "title": s["title"],
                "topics": [{"id": t["id"], "title": t["title"], "placement": t.get("placement", "main")} for t in s["topics"]],
            }
            for sid, s in cfg["sections"].items()
        ],
    }


def warm_up():
    """Fill the cache in the background right after start-up."""
    jobs = [lambda s=s: get_news(s) for s in config()["sections"]]
    jobs += [lambda lg=lg: get_league(lg) for lg in LEAGUES]
    jobs += [get_markets, get_fantasy, get_picks]
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
    server_version = "WorldNews/1.0"

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
        if route == "news":
            data = get_news(arg, force)
        elif route == "sports":
            data = get_league(arg, force)
        elif route == "fantasy":
            data = get_fantasy(force)
        elif route == "markets":
            data = get_markets(force)
        elif route == "picks":
            data = get_picks(arg, force)
        else:
            data = None
        if data is None:
            return self._error(404, "Unknown endpoint")
        return self._json(data)

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
    log.info("World News on http://localhost:%d", port)
    if not args.no_warmup:
        threading.Thread(target=warm_up, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        cache._save()


if __name__ == "__main__":
    main()
