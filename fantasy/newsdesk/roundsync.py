"""Bring player stats and prices up to date after each EuroLeague round.

Stats: box scores are cached for good the first time they are read, often
minutes after the buzzer, so each finished round is fetched once more when the
official numbers have settled. That picks up late stat corrections.

Prices: the official game moves prices some time after a round, with no fixed
hour and no timestamp in the feed. So the current prices are compared with the
ones from before the round ended, until enough of them differ. A check that
finds no change after the next round has tipped off gives up on that round.

Nothing here runs by itself: a systemd timer calls `fantasy sync` on Thursday
and Saturday mornings, the days after rounds usually finish.

The bookkeeping is a plain dict kept by the server in round-sync.json:
    {"season": "E2026", "from_round": 10, "rounds": {"10": {...}}}
"""

import json
import time
from collections import defaultdict

STATS_DELAY = 5 * 3600  # seconds after the last tip-off before stats count as settled
MIN_PRICE_MOVES = 20  # fewer changes than this are one-off fixes, not a round's update


def finished_rounds(games):
    """{round: its games} for the rounds where every game is over."""
    rounds = defaultdict(list)
    for g in games:
        rounds[g["round"]].append(g)
    return {r: gs for r, gs in rounds.items() if all(g["state"] == "post" for g in gs)}


def price_baseline(path, ts):
    """Prices from the latest daily snapshot on or before the local day of ts,
    or None when there is no such snapshot."""
    day = time.strftime("%Y-%m-%d", time.localtime(ts))
    best = None
    try:
        with open(path) as f:
            for line in f:
                snap = json.loads(line)
                if snap["day"] <= day:
                    best = snap["prices"]
    except (OSError, ValueError, KeyError):
        return best
    return best


def count_moves(base, prices):
    return sum(1 for i, p in prices.items() if i in base and base[i] != p)


def advance(state, season, games, prices, now, refetch, baseline):
    """Do whatever is due. Returns (state, report).

    prices: {player id: current price}. refetch(games) fetches a round's box
    scores again and returns True when all of them came back. baseline(ts)
    returns the prices from before a round that ended at ts, or None.
    report lists the rounds whose stats and prices were synced by this call.
    """
    done = finished_rounds(games)
    if not state or state.get("season") != season:
        # First run of a season: earlier rounds are history, only the latest one needs syncing.
        state = {"season": season, "from_round": max(done, default=0), "rounds": {}}

    first_tip = defaultdict(lambda: float("inf"))
    for g in games:
        first_tip[g["round"]] = min(first_tip[g["round"]], g["ts"])

    report = {"stats": [], "prices": []}
    for r in sorted(done):
        if r < state["from_round"]:
            continue
        entry = state["rounds"].setdefault(str(r), {})
        last_tip = max(g["ts"] for g in done[r])

        if not entry.get("stats_at") and now >= last_tip + STATS_DELAY and refetch(done[r]):
            entry["stats_at"] = now
            report["stats"].append(r)

        if entry.get("prices_at") or entry.get("prices_missed"):
            continue
        if "base" not in entry:
            entry["base"] = baseline(last_tip) or dict(prices)
        moves = count_moves(entry["base"], prices)
        if moves >= MIN_PRICE_MOVES:
            entry.update(prices_at=now, moves=moves)
            del entry["base"]
            report["prices"].append(r)
        elif now >= first_tip[r + 1]:
            entry["prices_missed"] = True
            del entry["base"]
    return state, report


def status(state):
    """What the site shows about the most recent round being synced."""
    rounds = (state or {}).get("rounds")
    if not rounds:
        return None
    r = max(rounds, key=int)
    e = rounds[r]
    return {
        "round": int(r),
        "stats_at": e.get("stats_at"),
        "prices_at": e.get("prices_at"),
        "price_moves": e.get("moves"),
        "prices_missed": bool(e.get("prices_missed")),
    }
