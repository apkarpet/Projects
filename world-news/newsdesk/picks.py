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

# Settings were tuned on rounds 4-7 and checked on rounds 8-9 (2026-27).
# Team offensive/defensive rating, missing opposing defenders, a usage boost
# for injured players' teammates and game pace were all tested the same way
# and did not beat noise, so they stay at 0 (shown on the page as context).
# Bump MODEL_VERSION whenever the model changes so the backtest reruns.
MODEL_VERSION = 6

FEIQ = "https://www.fantasyedgeiq.com"
CET = ZoneInfo("Europe/Paris")

PRIOR_MINUTES = 160  # how strongly last season's rate anchors this season's
RECENT_EXTRA = 0.0  # extra weight on the last 3 EuroLeague games (backtests found none helps)
DOMESTIC_WEIGHT = 0.3  # domestic minutes count 30% as much as EuroLeague ones
DOMESTIC_EST_WEIGHT = 0.2  # ...and less when PIR had to be estimated
AVAILABILITY = {0: 0.0, 1: 0.4, 2: 0.75, 3: 0.95}  # by injury severity
MAX_INHERITED = 6.0  # cap on minutes a player can inherit from injured teammates
EWMA_ALPHA = 0.3  # how fast minutes forget older games
DOMESTIC_MIN_SHARE = 0.0  # weight of recent domestic minutes in projected minutes
DVP_STRENGTH = 1.0  # how much of the opponent's position effect to apply
DVP_SHRINK = 4  # games of evidence before trusting it halfway
DVP_STAT = "pir"  # which stat "allowed by position" is measured in: pir or pts
PACE_STRENGTH = 0.0  # how much of the expected game pace to apply
DRTG_STRENGTH = 0.0  # opponent's defensive rating (points allowed per 100 possessions)
ORTG_STRENGTH = 0.0  # own team's offensive rating
MISSING_DEF_STRENGTH = 0.0  # boost when the opponent is missing rotation players
MISSING_DEF_WEIGHTED = True  # weight missing players by their defensive activity
USAGE_BOOST = 0.0  # teammates' PIR per minute rises with the share of team production that is out
SAME_POS_SHARE = 0.55  # share of an injured player's minutes going to his position
ROTATION_SHARE = 0.2  # share spread across the whole rotation
WIN_BONUS = 0.10  # official game: +10% PIR when the player's team wins
SLOTS = {"captain": 2.0, "starter": 1.0, "sixth": 1.0, "bench": 0.5}  # official multipliers
HOME_EDGE_POINTS = 3.0  # home court in points, for win chances
MARGIN_SD = 11.0  # spread of final margins around the expected one
RATING_SHRINK = 3  # games before a team's net rating is trusted halfway
PRICE_PRIOR = 0.0  # pull towards what his preseason price implies (0 = off)
CALIBRATION = 0.9  # overall scale; PIR is right-skewed, so the MAE-optimal value is a bit below 1


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
                "price_base": _f(r.get("price_base")),
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
        allowed[r["opp"]][pos][r["game"]] += r[DVP_STAT]
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
            shrink = len(games) / (len(games) + DVP_SHRINK)
            dvp[t][p] = (max(0.85, min(1.15, 1 + DVP_STRENGTH * (ratio - 1) * shrink)), len(games))
    # rank 1 = most generous defence for that position
    ranks = {}
    for p in ("G", "F", "C"):
        order = sorted(dvp, key=lambda t: -dvp[t][p][0])
        for i, t in enumerate(order, 1):
            ranks[(t, p)] = i
    # possessions per game: FGA - OREB + TOV + 0.44 FTA, from both teams' lines
    poss = defaultdict(lambda: defaultdict(float))
    for r in logs:
        poss[r["team"]][r["game"]] += r.get("fga", 0) - r.get("oreb", 0) + r.get("tov", 0) + 0.44 * r.get("fta", 0)
    pace = {t: statistics.mean(g.values()) for t, g in poss.items() if g}
    # offensive / defensive rating: points per 100 possessions, for and against
    pts = defaultdict(lambda: defaultdict(float))
    game_teams = defaultdict(set)
    for r in logs:
        pts[r["team"]][r["game"]] += r["pts"]
        game_teams[r["game"]].add(r["team"])
    ortg, drtg = {}, {}
    for t, games_ in poss.items():
        p_for = sum(pts[t].values())
        n_for = sum(games_.values())
        p_against = n_against = 0.0
        for gid in games_:
            for o in game_teams[gid] - {t}:
                p_against += pts[o][gid]
                n_against += poss[o][gid]
        if n_for and n_against:
            ortg[t] = 100 * p_for / n_for
            drtg[t] = 100 * p_against / n_against
    league_rtg = statistics.mean(ortg.values()) if ortg else 100.0
    # defensive activity per minute by position: steals, blocks, defensive rebounds
    dmin, dact = defaultdict(float), defaultdict(float)
    for r in logs:
        pos = posmap.get(r["key"]) or r.get("pos") or "F"
        dmin[pos] += r["min"]
        dact[pos] += r.get("stl", 0) + r.get("blk", 0) + 0.5 * (r.get("reb", 0) - r.get("oreb", 0))
    def_rate = {p: dact[p] / dmin[p] for p in dmin if dmin[p]}
    # rank 1 = best offence / most generous defence (easiest to score against)
    ortg_rank = {t: i for i, t in enumerate(sorted(ortg, key=lambda t: -ortg[t]), 1)}
    drtg_rank = {t: i for i, t in enumerate(sorted(drtg, key=lambda t: -drtg[t]), 1)}
    pace_n = {t: len(g) for t, g in poss.items()}
    league_pace = statistics.mean(pace.values()) if pace else 1.0
    return {
        "rate": rate, "home_edge": edge, "dvp": dvp, "dvp_rank": ranks, "teams": len(dvp),
        "pace": pace, "pace_n": pace_n, "league_pace": league_pace,
        "ortg": ortg, "drtg": drtg, "league_rtg": league_rtg, "def_rate": def_rate,
        "ortg_rank": ortg_rank, "drtg_rank": drtg_rank,
    }


def rating_factor(ctx, team, opp):
    """Own offence and opponent defence relative to league average."""
    f = 1.0
    lr = ctx["league_rtg"]
    if DRTG_STRENGTH and opp in ctx["drtg"]:
        n = ctx["pace_n"].get(opp, 0)
        f *= 1 + DRTG_STRENGTH * (ctx["drtg"][opp] / lr - 1) * n / (n + 4)
    if ORTG_STRENGTH and team in ctx["ortg"]:
        n = ctx["pace_n"].get(team, 0)
        f *= 1 + ORTG_STRENGTH * (ctx["ortg"][team] / lr - 1) * n / (n + 4)
    return f


def pace_factor(ctx, team, opp):
    """Expected possessions in this game relative to an average game."""
    if not PACE_STRENGTH or team not in ctx["pace"] or opp not in ctx["pace"]:
        return 1.0
    lp = ctx["league_pace"]

    def rel(t):
        n = ctx["pace_n"][t]
        return 1 + (ctx["pace"][t] / lp - 1) * n / (n + 4)

    expected = (rel(team) + rel(opp)) / 2
    return 1 + PACE_STRENGTH * (expected - 1)


def _ewma(values, alpha=None):
    alpha = EWMA_ALPHA if alpha is None else alpha
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
    ratings = team_ratings(games, cutoff)

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

    # what preseason prices say about PIR per minute (fit on games before cutoff)
    price_fit = None
    if PRICE_PRIOR:
        xs, ys, ws = [], [], []
        for p in players:
            el_ = by_key.get(p["key"], [])
            mins_ = sum(x["min"] for x in el_)
            if p.get("price_base") and mins_ >= 40:
                xs.append(p["price_base"])
                ys.append(sum(x["pir"] for x in el_) / mins_)
                ws.append(mins_)
        if len(xs) >= 30:
            mx = sum(x * w for x, w in zip(xs, ws)) / sum(ws)
            my = sum(y * w for y, w in zip(ys, ws)) / sum(ws)
            sxx = sum(w * (x - mx) ** 2 for x, w in zip(xs, ws))
            sxy = sum(w * (x - mx) * (y - my) for x, y, w in zip(xs, ys, ws))
            slope = sxy / sxx if sxx else 0.0
            price_fit = (my - slope * mx, slope)

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
                minutes = (1 - DOMESTIC_MIN_SHARE) * minutes + DOMESTIC_MIN_SHARE * m_dom
            if missed >= 2:
                minutes *= 0.5
                reasons.append(f"Has sat out the last {missed} EuroLeague games")
            elif missed == 1:
                minutes *= 0.85
                reasons.append("Missed his team's last EuroLeague game")
        elif team_played >= 3:
            # his team has played several EuroLeague games without him:
            # he is outside the EuroLeague rotation, whatever he plays at home
            minutes = 2.0
            reasons.append(f"Has not played in any of his team's {team_played} EuroLeague games")
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
        if price_fit and p.get("price_base"):
            rate = (1 - PRICE_PRIOR) * rate + PRICE_PRIOR * max(0.0, price_fit[0] + price_fit[1] * p["price_base"])

        # --- matchup and venue
        dvp, dvp_games = ctx["dvp"].get(opp["code"], {}).get(p["pos"], (1.0, 0))
        venue = ctx["home_edge"] if is_home else 1 / ctx["home_edge"]
        pace = pace_factor(ctx, p["team"], opp["code"])
        ratings_f = rating_factor(ctx, p["team"], opp["code"])

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
                "pace": pace,
                "ratings_f": ratings_f,
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
            pools = ((same, SAME_POS_SHARE), (healthy, ROTATION_SHARE))
            for pool, share in pools:
                tot = sum(r["minutes"] for r in pool)
                if not tot:
                    continue
                for r in pool:
                    room = MAX_INHERITED - sum(x for _, x in r["vacated"])
                    extra = min(freed * share * r["minutes"] / tot, max(0.0, room))
                    r["minutes"] += extra
                    r["vacated"].append((gone["p"]["name"], extra))

    # production the team just lost, as a share of what it usually produces
    lost_share = {}
    for team, members in by_team.items():
        team_logs = [x for x in logs if x["team"] == team]
        n_games = len({x["game"] for x in team_logs})
        if not n_games:
            continue
        team_pir = sum(x["pir"] for x in team_logs) / n_games
        last_game = team_games.get(team, [None])[-1] if team_games.get(team) else None
        lost = 0.0
        for r in members:
            if r["avail"] <= 0.4 and r["el"] and last_game is not None and r["el"][-1]["ts"] >= last_game:
                recent = r["el"][-6:]
                lost += max(0.0, statistics.mean(x["pir"] for x in recent)) * (1 - r["avail"])
        if team_pir > 0:
            lost_share[team] = min(0.5, lost / team_pir)

    # opponents missing rotation players (just ruled out) defend worse
    missing = defaultdict(float)
    missing_names = defaultdict(list)
    for team, members in by_team.items():
        last_game = team_games.get(team, [None])[-1] if team_games.get(team) else None
        for r in members:
            if r["avail"] > 0.4 or not r["el"] or last_game is None or r["el"][-1]["ts"] < last_game:
                continue
            el_ = r["el"][-6:]
            mins_ = sum(x["min"] for x in el_)
            if not mins_ or mins_ / len(el_) < 12:
                continue
            weight = 1.0
            if MISSING_DEF_WEIGHTED:
                act = sum(x.get("stl", 0) + x.get("blk", 0) + 0.5 * (x.get("reb", 0) - x.get("oreb", 0)) for x in el_) / mins_
                base = ctx["def_rate"].get(r["p"]["pos"]) or act or 1
                weight = act / base if base else 1.0
            missing[team] += (mins_ / len(el_)) / 200 * weight * (1 - r["avail"])
            missing_names[team].append(r["p"]["name"])

    out = []
    for r in rows:
        p = r["p"]
        minutes = min(r["minutes"], 34.0)
        r["usage_f"] = 1 + USAGE_BOOST * lost_share.get(p["team"], 0.0) if r["avail"] > 0.4 else 1.0
        if USAGE_BOOST and lost_share.get(p["team"], 0) >= 0.1 and r["avail"] > 0.4 and r["minutes"] >= 10:
            r["reasons"].append(f"{round(lost_share[p['team']] * 100)}% of his team's usual PIR is sidelined, so more shots and touches")
        opp_missing = missing.get(r["opp"]["code"], 0.0)
        r["missing_f"] = 1 + MISSING_DEF_STRENGTH * opp_missing
        if MISSING_DEF_STRENGTH and opp_missing >= 0.05:
            r["reasons"].append(f"{r['opp']['name']} are without {', '.join(missing_names[r['opp']['code']])}")
        proj = minutes * r["rate"] * r["dvp"] * r["venue"] * r["pace"] * r["ratings_f"] * r["missing_f"] * r["usage_f"] * r["avail"] * CALIBRATION
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
        win, _ = win_prob(ratings, p["team"], r["opp"]["code"], r["home"])
        xfp = proj * (1 + WIN_BONUS * win)
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
                "win": round(win * 100),
                "xfp": round(xfp, 1),
                "avail": round(r["avail"], 2),
                "sd": round(sd, 2),
                "value": round(xfp / price, 2) if price else None,
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
                "pace": round(r["pace"], 3),
                "ortg": round(ctx["ortg"][p["team"]], 1) if p["team"] in ctx["ortg"] else None,
                "ortg_rank": ctx["ortg_rank"].get(p["team"]),
                "opp_drtg": round(ctx["drtg"][r["opp"]["code"]], 1) if r["opp"]["code"] in ctx["drtg"] else None,
                "opp_drtg_rank": ctx["drtg_rank"].get(r["opp"]["code"]),
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


# ---------------------------------------------------------------- win chances


def team_ratings(games, cutoff=float("inf")):
    """Average point margin per team from finished games before cutoff,
    shrunk towards zero while the sample is small."""
    net = defaultdict(lambda: [0.0, 0])
    for g in games:
        if g["state"] != "post" or g["ts"] >= cutoff:
            continue
        d = g["home"]["score"] - g["away"]["score"]
        net[g["home"]["code"]][0] += d
        net[g["home"]["code"]][1] += 1
        net[g["away"]["code"]][0] -= d
        net[g["away"]["code"]][1] += 1
    return {t: tot / (n + RATING_SHRINK) for t, (tot, n) in net.items()}


def win_prob(ratings, team, opp, home):
    spread = ratings.get(team, 0.0) - ratings.get(opp, 0.0) + (HOME_EDGE_POINTS if home else -HOME_EDGE_POINTS)
    return 0.5 * (1 + math.erf(spread / (MARGIN_SD * math.sqrt(2)))), spread


def coach_rows(players, games, rnd):
    """Coaches score on results, so rank them by win chance."""
    ratings = team_ratings(games)
    fixtures = _round_games(games, rnd)
    out = []
    for p in players:
        if p["pos"] != "HC" or p["team"] not in fixtures:
            continue
        g, home = fixtures[p["team"]]
        opp = g["away"] if home else g["home"]
        win, spread = win_prob(ratings, p["team"], opp["code"], home)
        out.append(
            {
                "key": p["key"],
                "name": p["name"],
                "team": p["team"],
                "price": p["price"],
                "popularity": p["popularity"],
                "opp": opp["code"],
                "tip": g["ts"],
                "home": home,
                "win": round(win * 100),
                "spread": round(spread, 1),
            }
        )
    out.sort(key=lambda c: -c["win"])
    return out


# ---------------------------------------------------------------- lists


def suggestions(rows):
    """Short lists, all ranked by expected fantasy points (PIR plus the
    expected win bonus)."""
    able = [r for r in rows if (r["severity"] is None or r["severity"] >= 2) and r["xfp"] > 0]
    sure = [r for r in able if r["severity"] is None or r["severity"] >= 3]
    by_xfp = sorted(able, key=lambda r: -r["xfp"])
    values = sorted((r["value"] for r in able if r["value"] and r["xfp"] >= 6), reverse=True)
    median_value = statistics.median(values) if values else 1.0
    pick = lambda rs, n=10: [r["key"] + "|" + r["team"] for r in rs[:n]]
    return {
        # captain points double, so only players with no injury doubt
        "captains": pick(sorted(sure, key=lambda r: -r["xfp"]), 3),
        "top": pick(by_xfp),
        "value": pick(sorted([r for r in able if r["xfp"] >= 9], key=lambda r: -(r["value"] or 0))),
        "differentials": pick([r for r in by_xfp if r["popularity"] < 8 and r["xfp"] >= 12]),
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


def _winners(games):
    """(game id, team code) -> True if that team won."""
    won = {}
    for g in games:
        if g["state"] == "post" and g.get("winner"):
            w = g["winner"]
            won[(g["id"], g["home"]["code"])] = w == "home"
            won[(g["id"], g["away"]["code"])] = w == "away"
    return won


def fantasy_points(log_row, won):
    return log_row["pir"] * (1 + WIN_BONUS * won.get((log_row["game"], log_row["team"]), False))


def score_round(pred, actual):
    """pred: list of dicts with key, team, proj, xfp (and baselines).
    actual: {(key, team): {"pir": .., "fp": ..}}. Ranks are judged in fantasy points."""
    pairs = [(r, actual[(r["key"], r["team"])]) for r in pred if (r["key"], r["team"]) in actual]
    if not pairs:
        return None

    def top(metric, n):
        best = sorted(pairs, key=lambda x: -(x[0].get(metric) or 0))[:n]
        return round(statistics.mean(a["fp"] for _, a in best), 2)

    return pairs, top


def backtest(players, logs, domestic, games, min_round=4):
    """Replay the model on finished rounds using only earlier data. Average
    miss is measured in PIR; pick quality in official fantasy points (PIR
    plus the 10% win bonus)."""
    rounds = sorted({g["round"] for g in games if g["state"] == "post"})
    done = [r for r in rounds if all(g["state"] == "post" for g in games if g["round"] == r)]
    won = _winners(games)
    results, briers = [], []
    for rnd in done:
        if rnd < min_round:
            continue
        cutoff = first_tip(games, rnd)
        rows, _ = project(players, logs, domestic, games, rnd, cutoff)
        actual = {(r["key"], r["team"]): {"pir": r["pir"], "fp": fantasy_points(r, won)} for r in logs if r["round"] == rnd}
        others = defaultdict(list)  # every other game of the season, past and future
        for r in logs:
            if r["round"] != rnd:
                others[(r["key"], r["team"])].append(r["pir"])
        pred = [
            {**r, "hindsight": statistics.mean(others[(r["key"], r["team"])])}
            for r in rows
            if r["season"] is not None and others.get((r["key"], r["team"]))
        ]
        scored = score_round(pred, actual)
        if not scored or len(scored[0]) < 30:
            continue
        pairs, top = scored

        def mae(metric):
            return round(statistics.mean(abs(r[metric] - a["pir"]) for r, a in pairs), 2)

        def corr(metric):
            try:
                return round(statistics.correlation([r[metric] for r, _ in pairs], [a["fp"] for _, a in pairs], method="ranked"), 3)
            except statistics.StatisticsError:
                return 0.0

        entry = {"round": rnd, "players": len(pairs), "best_captain": round(max(a["fp"] for _, a in pairs), 1)}
        for name, metric in (("model", "proj"), ("season", "season"), ("last3", "l3")):
            rank_metric = "xfp" if name == "model" else metric
            entry[name] = {
                "mae": mae(metric),
                "corr": corr(rank_metric),
                "top10": top(rank_metric, 10),
                "top20": top(rank_metric, 20),
                "captain": top(rank_metric, 1),
            }
        entry["hindsight"] = {"mae": mae("hindsight")}
        results.append(entry)

        ratings = team_ratings(games, cutoff)
        for g in games:
            if g["round"] == rnd and g["state"] == "post":
                p, _ = win_prob(ratings, g["home"]["code"], g["away"]["code"], True)
                briers.append((p - (g["winner"] == "home")) ** 2)

    summary = {}
    if results:
        for k in ("model", "season", "last3"):
            summary[k] = {
                m: round(statistics.mean(r[k][m] for r in results), 3 if m == "corr" else 2)
                for m in ("mae", "corr", "top10", "top20", "captain")
            }
        summary["hindsight"] = {"mae": round(statistics.mean(r["hindsight"]["mae"] for r in results), 2)}
        summary["best_captain"] = round(statistics.mean(r["best_captain"] for r in results), 1)
    if briers:
        summary["win_brier"] = round(statistics.mean(briers), 3)
    return {"rounds": results, "summary": summary}


# ---------------------------------------------------------------- live tracking


def save_snapshot(directory, payload):
    """Keep the latest pre-lock projections for a round so they can be
    scored once the round is played."""
    import os

    os.makedirs(directory, exist_ok=True)
    snap = {
        "round": payload["round"],
        "saved_at": time.time(),
        "model_version": MODEL_VERSION,
        "lists": payload["lists"],
        "players": [
            {k: r[k] for k in ("key", "team", "name", "proj", "xfp", "price", "popularity", "value", "season", "l3")}
            for r in payload["players"]
        ],
    }
    path = os.path.join(directory, f"round-{payload['round']:02d}.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(snap, f)
    os.replace(tmp, path)


def track_record(directory, logs, games):
    """Score every saved snapshot whose round is finished."""
    import glob
    import os

    won = _winners(games)
    out = []
    for path in sorted(glob.glob(os.path.join(directory, "round-*.json"))):
        try:
            with open(path) as f:
                snap = json.load(f)
        except (OSError, ValueError):
            continue
        rnd = snap["round"]
        rgames = [g for g in games if g["round"] == rnd]
        if not rgames or any(g["state"] != "post" for g in rgames):
            out.append({"round": rnd, "saved_at": snap["saved_at"], "pending": True})
            continue
        actual = {(r["key"], r["team"]): {"pir": r["pir"], "fp": fantasy_points(r, won)} for r in logs if r["round"] == rnd}
        scored = score_round(snap["players"], actual)
        if not scored:
            continue
        pairs, top = scored
        by = {(r["key"], r["team"]): r for r in snap["players"]}

        def listed(name):
            keys = [tuple(k.split("|")) for k in snap["lists"].get(name, [])]
            got = [(by[k], actual[k]) for k in keys if k in by and k in actual]
            return got

        value = listed("value")
        caps = listed("captains")
        out.append(
            {
                "round": rnd,
                "saved_at": snap["saved_at"],
                "pending": False,
                "players": len(pairs),
                "mae": round(statistics.mean(abs(r["proj"] - a["pir"]) for r, a in pairs), 2),
                "season_mae": round(statistics.mean(abs((r["season"] or 0) - a["pir"]) for r, a in pairs), 2),
                "top20": top("xfp", 20),
                "season_top20": top("season", 20),
                "captain": caps[0][1]["fp"] if caps else None,
                "captain_name": caps[0][0]["name"] if caps else None,
                "best_captain": round(max(a["fp"] for _, a in pairs), 1),
                "value_per_credit": round(sum(a["fp"] for _, a in value) / sum(r["price"] for r, _ in value), 2) if value else None,
                "avg_per_credit": round(sum(a["fp"] for _, a in pairs) / sum(r["price"] for r, _ in pairs), 2),
            }
        )
    return out


# ---------------------------------------------------------------- my team

ROSTER = {"G": 4, "F": 4, "C": 2, "HC": 1}
HORIZON_WEIGHTS = (1.0, 0.6, 0.4)  # this round, next round, the one after


def lineup_value(points):
    """Best lineup score for ten players' expected points: the top scorer
    captains (x2), the next five are starters and sixth man (x1) and the
    other four sit on the bench (x0.5). Assumes any five positions can start."""
    xs = sorted(points, reverse=True)
    return 2 * xs[0] + sum(xs[1:6]) + 0.5 * sum(xs[6:]) if xs else 0.0


def best_lineup(ids, points):
    order = sorted(ids, key=lambda i: -points.get(i, 0.0))
    return {"captain": order[0] if order else None, "starters": order[:5], "sixth": order[5] if len(order) > 5 else None, "bench": order[6:]}


def optimize_transfers(roster, info, weighted, budget, max_moves, beam=30, pool_size=28):
    """Beam search over sell/buy pairs at the same position.

    roster: player ids (key|team); info: id -> {"pos", "price"};
    weighted: list of (weight, {id: expected points}) per round.
    Returns the best roster found for each number of moves 1..max_moves."""

    def score(ros):
        return sum(w * lineup_value([pts.get(i, 0.0) for i in ros]) for w, pts in weighted)

    def cost(ros):
        return sum(info[i]["price"] for i in ros)

    blended = defaultdict(float)
    for w, pts in weighted:
        for i, v in pts.items():
            blended[i] += w * v
    pool = defaultdict(list)
    for pos in ("G", "F", "C"):
        cands = [i for i in info if info[i]["pos"] == pos and i not in roster]
        by_pts = sorted(cands, key=lambda i: -blended.get(i, 0.0))[:pool_size]
        by_val = sorted(
            (i for i in cands if blended.get(i, 0.0) >= 5),
            key=lambda i: -blended.get(i, 0.0) / max(info[i]["price"], 1),
        )[: pool_size // 2]
        pool[pos] = list(dict.fromkeys(by_pts + by_val))

    start = frozenset(roster)
    base = score(start)
    frontier = [(base, start, ())]
    best_by_k = {}
    seen = {start}
    for k in range(1, max_moves + 1):
        cand = []
        for _, ros, moves in frontier:
            bought = {m[1] for m in moves}
            for out in ros:
                if out in bought:
                    continue
                for inn in pool[info[out]["pos"]]:
                    if inn in ros:
                        continue
                    new = (ros - {out}) | {inn}
                    if new in seen or cost(new) > budget + 1e-9:
                        continue
                    seen.add(new)
                    cand.append((score(new), new, moves + ((out, inn),)))
        if not cand:
            break
        cand.sort(key=lambda c: -c[0])
        frontier = cand[:beam]
        top = frontier[0]
        prev = best_by_k.get(k - 1, (base, start, ()))
        best_by_k[k] = top if top[0] > prev[0] else prev
    out = []
    for k, (sc, ros, moves) in sorted(best_by_k.items()):
        if not moves or sc <= base + 0.05:
            continue
        if out and out[-1]["moves"] == [list(m) for m in moves]:
            continue
        out.append(
            {
                "transfers": len(moves),
                "moves": [list(m) for m in moves],
                "gain": round(sc - base, 1),
                "cost": round(cost(ros), 1),
                "bank": round(budget - cost(ros), 1),
            }
        )
    return {"base": round(base, 1), "options": out}


def gameday_subs(lineup, entries, min_gain=1.0):
    """Best subs for the rest of a round in progress.

    entries: id -> {"value": points (actual once his game has started,
    expected before), "locked": True once his game has started, "tip"}.
    Rules: a starter whose game has started can only move to the bench, a
    bench player whose game has started cannot come in, and the captain
    must start. Swaps worth less than min_gain points are left out because
    the projections are not that precise."""
    ones = list(lineup["starters"]) + [lineup["sixth"]]
    bench = list(lineup["bench"])
    cap = lineup["captain"]
    val = lambda i: entries.get(i, {}).get("value", 0.0)
    locked = lambda i: entries.get(i, {}).get("locked", False)

    new_cap = cap
    if not locked(cap):
        starters_open = [i for i in lineup["starters"] if not locked(i)]
        best = max(starters_open, key=val, default=cap)
        if val(best) > val(cap) + min_gain:
            new_cap = best

    # pair the weakest full-point players with the strongest bench players who can still come in
    out_pool = sorted((i for i in ones if i != new_cap), key=val)
    in_pool = sorted((i for i in bench if not locked(i)), key=lambda i: -val(i))
    moves = []
    for out, inn in zip(out_pool, in_pool):
        gain = 0.5 * (val(inn) - val(out))
        if gain < min_gain:
            break
        # decide before the first of the two games that has not started yet
        tips = [entries.get(i, {}).get("tip") for i in (out, inn) if not locked(i)]
        tips = [t for t in tips if t]
        moves.append({"out": out, "in": inn, "gain": round(gain, 1), "by": min(tips) if tips else None})

    starters = list(lineup["starters"])
    sixth = lineup["sixth"]
    bench_new = list(bench)
    for m in moves:
        if m["out"] in starters:
            starters[starters.index(m["out"])] = m["in"]
        else:
            sixth = m["in"]
        bench_new[bench_new.index(m["in"])] = m["out"]
    gain = sum(m["gain"] for m in moves)
    if new_cap != cap:
        gain += val(new_cap) - val(cap)
    return {
        "moves": moves,
        "captain": new_cap if new_cap != cap else None,
        "gain": round(gain, 1),
        "lineup": {"captain": new_cap, "starters": starters, "sixth": sixth, "bench": bench_new},
    }


def rotation_absences(logs, rnd):
    """Rotation players (10+ minutes in their team's previous game) who did
    not play in round rnd. Used as a stand-in for the injury report when
    replaying past rounds."""
    played = {(r["key"], r["team"]) for r in logs if r["round"] == rnd}
    teams = {r["team"] for r in logs if r["round"] == rnd}
    out = {}
    for t in teams:
        prev = [r for r in logs if r["team"] == t and r["round"] < rnd]
        if not prev:
            continue
        last = max(r["round"] for r in prev)
        for r in prev:
            if r["round"] == last and r["min"] >= 10 and (r["key"], t) not in played:
                out[r["key"]] = {"severity": 0, "status": "Out", "comment": "did not play"}
    return out
