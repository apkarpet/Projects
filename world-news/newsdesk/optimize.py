"""Team building for the EuroLeague Fantasy Challenge.

1. Exact optimisation (mixed-integer programming with scipy/HiGHS): choose
   the roster that maximises expected lineup points over one or more
   rounds, where each round's lineup (captain x2, four starters and sixth
   man x1, four on the bench x0.5) is chosen together with the roster,
   subject to budget, positions (4 G, 4 F, 2 C) and a transfer limit.

2. Monte Carlo round simulation: plays a round thousands of times with
   uncertain scores and availability, and applies the morning-sub rules
   day by day, the way a manager would. This values things a single
   projection cannot, like a bench player whose game comes after the
   starters' (insurance), or a doubtful starter whose news arrives the
   morning of his game.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

ATHENS = ZoneInfo("Europe/Athens")
ROSTER = {"G": 4, "F": 4, "C": 2}
MULT_CAPTAIN, MULT_FULL, MULT_BENCH = 2.0, 1.0, 0.5
FULL_SLOTS = 5  # four starters next to the captain, plus the sixth man


# ---------------------------------------------------------------- exact optimisation


def best_roster(players, rounds, budget, current=None, max_transfers=None, exclude=()):
    """players: id -> {"pos", "price"}.
    rounds: list of (weight, {id: expected points}).
    current: ids of the team now (transfers are counted against it).
    exclude: rosters (sets of ids) that may not be returned again.
    Returns {"roster": [...], "lineups": [...], "value": float} or None."""
    ids = [i for i in players if players[i]["pos"] in ROSTER]
    n, R = len(ids), len(rounds)
    idx = {i: k for k, i in enumerate(ids)}
    # variable layout: x (n) | per round: captain (n), full (n), bench (n)
    nv = n * (1 + 3 * R)

    def var(kind, r, k):
        return n + r * 3 * n + kind * n + k

    c = np.zeros(nv)
    for r, (w, pts) in enumerate(rounds):
        for i, k in idx.items():
            v = pts.get(i, 0.0)
            c[var(0, r, k)] = -w * MULT_CAPTAIN * v
            c[var(1, r, k)] = -w * MULT_FULL * v
            c[var(2, r, k)] = -w * MULT_BENCH * v

    rows = []
    lo, hi = [], []
    A = lil_matrix((3 + 1 + 1 + n * R + 2 * R + len(exclude), nv))
    row = 0
    for pos, count in ROSTER.items():
        for i, k in idx.items():
            if players[i]["pos"] == pos:
                A[row, k] = 1
        lo.append(count)
        hi.append(count)
        row += 1
    for i, k in idx.items():
        A[row, k] = players[i]["price"]
    lo.append(0)
    hi.append(budget + 1e-6)
    row += 1
    if current is not None and max_transfers is not None:
        cur = set(current)
        for i, k in idx.items():
            if i not in cur:
                A[row, k] = 1
        lo.append(0)
        hi.append(max_transfers)
    else:
        lo.append(0)
        hi.append(np.inf)
    row += 1
    for r in range(R):
        for k in range(n):  # each roster player has exactly one role
            A[row, var(0, r, k)] = 1
            A[row, var(1, r, k)] = 1
            A[row, var(2, r, k)] = 1
            A[row, k] = -1
            lo.append(0)
            hi.append(0)
            row += 1
        for k in range(n):
            A[row, var(0, r, k)] = 1
        lo.append(1)
        hi.append(1)
        row += 1
        for k in range(n):
            A[row, var(1, r, k)] = 1
        lo.append(FULL_SLOTS)
        hi.append(FULL_SLOTS)
        row += 1
    for ros in exclude:
        for i in ros:
            if i in idx:
                A[row, idx[i]] = 1
        lo.append(0)
        hi.append(sum(ROSTER.values()) - 1)
        row += 1

    res = milp(
        c,
        constraints=LinearConstraint(A.tocsr(), lo, hi),
        integrality=np.ones(nv),
        bounds=Bounds(0, 1),
        options={"time_limit": 20},
    )
    if res.x is None:
        return None
    x = res.x
    roster = [i for i, k in idx.items() if x[k] > 0.5]
    lineups = []
    for r in range(R):
        cap = next(i for i in roster if x[var(0, r, idx[i])] > 0.5)
        full = [i for i in roster if x[var(1, r, idx[i])] > 0.5]
        full.sort(key=lambda i: -rounds[r][1].get(i, 0.0))
        bench = [i for i in roster if i != cap and i not in full]
        lineups.append({"captain": cap, "starters": [cap] + full[:4], "sixth": full[4], "bench": bench})
    return {"roster": roster, "lineups": lineups, "value": -res.fun}


def k_best_rosters(players, rounds, budget, current=None, max_transfers=None, k=5):
    """The k best different rosters (each found by excluding the previous ones)."""
    found, exclude = [], []
    for _ in range(k):
        sol = best_roster(players, rounds, budget, current, max_transfers, exclude)
        if not sol:
            break
        found.append(sol)
        exclude.append(set(sol["roster"]))
    return found


# ---------------------------------------------------------------- Monte Carlo


def game_day(ts):
    return datetime.fromtimestamp(ts, ATHENS).date() if ts else None


def simulate_round(roster, info, lineup=None, n=4000, seed=7, subs=True):
    """Expected lineup points for one round with daily subs.

    info: id -> {"mean": points if he plays (win bonus included on average),
    "sd", "p": chance he plays, "win": team win chance, "team", "tip"}.
    lineup: starting lineup (defaults to the best by expectation).
    Returns {"mean", "p10", "p90", "no_subs"}."""
    ids = list(roster)
    m = len(ids)
    rng = np.random.default_rng(seed)
    mean = np.array([info[i]["mean"] for i in ids])
    sd = np.array([max(info[i]["sd"], 1.0) for i in ids])
    p = np.array([info[i]["p"] for i in ids])
    days = [game_day(info[i]["tip"]) for i in ids]
    order = sorted({d for d in days if d})
    day_idx = np.array([order.index(d) if d else len(order) for d in days])

    # team results are shared by teammates: 10% bonus on a win
    teams = sorted({info[i]["team"] for i in ids})
    team_win = {t: rng.random(n) < next(info[i]["win"] for i in ids if info[i]["team"] == t) for t in teams}
    won = np.stack([team_win[info[i]["team"]] for i in ids], axis=1)
    win_p = np.array([info[i]["win"] for i in ids])
    base = mean / (1 + 0.1 * win_p)  # PIR if he plays, before the win bonus
    plays = rng.random((n, m)) < p
    raw = np.maximum(-8.0, rng.normal(base, sd, size=(n, m)))
    score = np.where(plays, raw * np.where(won, 1.1, 1.0), 0.0)
    expect = p * mean  # what a manager expects before news

    # starting lineup: by expectation unless given
    if lineup is None:
        top = list(np.argsort(-expect))
        cap0, full0 = top[0], top[1:6]
    else:
        cap0 = ids.index(lineup["captain"])
        full0 = [ids.index(i) for i in lineup["starters"] if i != lineup["captain"]] + [ids.index(lineup["sixth"])]

    def final_points(cap, full):
        mult = np.full((n, m), MULT_BENCH)
        mult[full] = MULT_FULL
        mult[np.arange(n), cap] = MULT_CAPTAIN
        return (score * mult).sum(axis=1)

    cap = np.full(n, cap0)
    full = np.zeros((n, m), dtype=bool)
    full[:, full0] = True
    no_subs = final_points(cap, full)
    if subs:
        for d in range(len(order)):
            started = day_idx < d  # games already played
            today = day_idx == d
            # morning value: real score if played, news-aware expectation today, expectation later
            val = np.where(started[None, :], score, np.where(today[None, :], plays * mean[None, :], expect[None, :]))
            cap_locked = started[cap]
            # bench players who have played cannot come in
            eligible = full | ~started[None, :]
            eligible[np.arange(n), cap] = True
            v = np.where(eligible, val, -1e9)
            # captain stays if his game has started; otherwise the best eligible non-started starter candidate
            # a new captain must be someone whose game has not started
            v_cap = np.where(~started[None, :] & eligible, val, -1e9)
            new_cap = np.where(cap_locked, cap, np.argmax(v_cap, axis=1))
            # fill the five full-point slots with the best remaining eligible players
            v2 = v.copy()
            v2[np.arange(n), new_cap] = -2e9
            take = np.argsort(-v2, axis=1)[:, :FULL_SLOTS]
            new_full = np.zeros_like(full)
            np.put_along_axis(new_full, take, True, axis=1)
            cap, full = new_cap, new_full
    pts = final_points(cap, full)
    return {
        "mean": round(float(pts.mean()), 1),
        "p10": round(float(np.percentile(pts, 10)), 1),
        "p90": round(float(np.percentile(pts, 90)), 1),
        "no_subs": round(float(no_subs.mean()), 1),
    }


def sim_info(rows):
    """Turn projection rows into simulator inputs."""
    info = {}
    for r in rows:
        avail = r.get("avail") or 0.0
        mean_if_plays = r["xfp"] / avail if avail > 0 else 0.0
        info[f"{r['key']}|{r['team']}"] = {
            "mean": mean_if_plays,
            "sd": r.get("sd") or 6.0,
            "p": avail,
            "win": (r.get("win") or 50) / 100,
            "team": r["team"],
            "tip": r.get("tip"),
        }
    return info


# ---------------------------------------------------------------- team backtest


def team_backtest(feiq_players, logs, domestic, games, budget=95.0, min_round=4, free_transfers=4):
    """Replay finished rounds: build a team with only what was known before
    each round and score it with what actually happened. Compares the model
    with building from season averages. Players who sat out a round are
    treated as known-out (a stand-in for that day's injury report)."""
    from . import picks  # local import: picks does not depend on this module

    rounds = sorted({g["round"] for g in games if g["state"] == "post"})
    done = [r for r in rounds if r >= min_round and all(g["state"] == "post" for g in games if g["round"] == r)]
    if not done:
        return None
    won = picks._winners(games)
    players = {f"{p['key']}|{p['team']}": {"pos": p["pos"], "price": p["price"]} for p in feiq_players if p["pos"] in ROSTER}

    def actual(rnd):
        return {f"{r['key']}|{r['team']}": picks.fantasy_points(r, won) for r in logs if r["round"] == rnd}

    def score(lineup, act):
        cap = lineup["captain"]
        full = [i for i in lineup["starters"] if i != cap] + [lineup["sixth"]]
        return 2 * act.get(cap, 0) + sum(act.get(i, 0) for i in full) + 0.5 * sum(act.get(i, 0) for i in lineup["bench"])

    out = {"rounds": [], "budget": budget}
    team = {"model": None, "season": None}
    totals = {"model": 0.0, "season": 0.0, "model_wc": 0.0, "season_wc": 0.0, "best": 0.0}
    for rnd in done:
        sat = picks.rotation_absences(logs, rnd)
        rows, _ = picks.project(feiq_players, logs, domestic, games, rnd, picks.first_tip(games, rnd), sat)
        act = actual(rnd)
        vals = {
            "model": {f"{r['key']}|{r['team']}": r["xfp"] for r in rows},
            "season": {f"{r['key']}|{r['team']}": (r["season"] or 0.0) * (0.0 if r["key"] in sat else 1.0) for r in rows},
        }
        entry = {"round": rnd}
        for how in ("model", "season"):
            wc = best_roster(players, [(1.0, vals[how])], budget)
            path = best_roster(players, [(1.0, vals[how])], budget, team[how], None if team[how] is None else free_transfers)
            team[how] = path["roster"]
            entry[f"{how}_wc"] = round(score(wc["lineups"][0], act), 1)
            entry[how] = round(score(path["lineups"][0], act), 1)
            totals[how] += entry[how]
            totals[f"{how}_wc"] += entry[f"{how}_wc"]
        best = best_roster(players, [(1.0, act)], budget)
        entry["best"] = round(best["value"], 1)
        totals["best"] += entry["best"]
        out["rounds"].append(entry)
    n = len(out["rounds"])
    out["average"] = {k: round(v / n, 1) for k, v in totals.items()}
    out["total"] = {k: round(v, 1) for k, v in totals.items()}
    return out
