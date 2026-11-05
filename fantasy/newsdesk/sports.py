"""Scores and standings: EuroLeague (official feeds), NBA (ESPN), Greek
Basket League (ESAKE website)."""

import html
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .net import fetch_json, fetch_text

ATHENS = ZoneInfo("Europe/Athens")
EASTERN = ZoneInfo("America/New_York")

EL_FEEDS = "https://feeds.incrowdsports.com/provider/euroleague-feeds"


def season_start_year(now=None):
    now = now or datetime.now(ATHENS)
    return now.year if now.month >= 8 else now.year - 1


def el_season():
    return f"E{season_start_year()}"


def pick_default_round(rounds):
    """rounds: ordered list of (key, games). Prefer the round in progress if
    any game has started or the first tip-off is within ~36h; otherwise show
    the last finished round."""
    if not rounds:
        return None
    now = time.time()
    current = None
    for key, games in rounds:
        if any(g["state"] != "post" for g in games):
            current = (key, games)
            break
    if current is None:
        return rounds[-1][0]
    key, games = current
    started = any(g["state"] != "pre" for g in games)
    first = min((g["ts"] for g in games if g["ts"]), default=now)
    idx = [k for k, _ in rounds].index(key)
    if started or first - now < 36 * 3600 or idx == 0:
        return key
    return rounds[idx - 1][0]


def has_live(payload):
    return any(g["state"] == "in" for r in payload.get("rounds", []) for g in r["games"])


# ---------------------------------------------------------------- EuroLeague


def _el_state(x):
    st = (x.get("status") or "").lower()
    if st == "result":
        return "post"
    if x.get("quarter") or st in ("live", "playing", "inprogress", "in_progress", "started"):
        return "in"
    return "pre"


def _el_side(s, state):
    return {
        "code": s.get("tla") or s.get("code"),
        "name": s.get("editorialName") or s.get("abbreviatedName") or s.get("name"),
        "full": s.get("name"),
        "crest": (s.get("imageUrls") or {}).get("crest"),
        "score": s.get("score") if state != "pre" else None,
    }


def el_games(season):
    data = fetch_json(f"{EL_FEEDS}/v2/competitions/E/seasons/{season}/games?limit=500")["data"]
    games = []
    for x in data:
        state = _el_state(x)
        ts = datetime.fromisoformat(x["date"].replace("Z", "+00:00")).timestamp()
        detail = None
        if state == "in":
            q = x.get("quarter")
            detail = f"Q{q}" if q else "Live"
            if x.get("remainingTime"):
                detail += f" {x['remainingTime']}"
        g = {
            "id": x["code"],
            "round": x["round"]["round"],
            "ts": ts,
            "state": state,
            "detail": detail,
            "home": _el_side(x["home"], state),
            "away": _el_side(x["away"], state),
        }
        if state == "post":
            g["winner"] = "home" if g["home"]["score"] > g["away"]["score"] else "away"
        games.append(g)
    games.sort(key=lambda g: (g["round"], g["ts"]))
    return games


def el_standings(season, games):
    xml = fetch_text(f"https://api-live.euroleague.net/v1/standings?seasonCode={season}")
    root = ET.fromstring(xml)
    by_name = {}
    for g in games:
        for side in (g["home"], g["away"]):
            by_name[side["full"]] = side
    rows = []
    for t in root.iter("team"):
        name = t.findtext("name")
        info = by_name.get(name, {})
        rows.append(
            {
                "rank": int(t.findtext("ranking") or 0),
                "name": info.get("name") or name,
                "full": name,
                "crest": info.get("crest"),
                "gp": int(t.findtext("totalgames") or 0),
                "w": int(t.findtext("wins") or 0),
                "l": int(t.findtext("losses") or 0),
                "diff": int(t.findtext("difference") or 0),
            }
        )
    rows.sort(key=lambda r: r["rank"])
    return rows


def euroleague():
    season = el_season()
    games = el_games(season)
    by_round = {}
    for g in games:
        by_round.setdefault(g["round"], []).append(g)
    ordered = sorted(by_round.items())
    default = pick_default_round(ordered)
    keys = [k for k, _ in ordered]
    idx = keys.index(default) if default in keys else 0
    window = ordered[max(0, idx - 1) : idx + 2]
    try:
        standings = el_standings(season, games)
    except Exception:  # noqa: BLE001 - scores are still useful without standings
        standings = []
    return {
        "league": "euroleague",
        "season": season,
        "rounds": [{"key": k, "label": f"Round {k}", "games": gs} for k, gs in window],
        "default": default,
        "standings": [{"label": "Regular season", "rows": standings, "lines": [6, 10]}],
    }


# ---------------------------------------------------------------- NBA (ESPN)

ESPN_NBA = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"


def _nba_game(e):
    c = e["competitions"][0]
    st = e["status"]["type"]
    state = st.get("state", "pre")
    g = {
        "id": e["id"],
        "ts": datetime.fromisoformat(e["date"].replace("Z", "+00:00")).timestamp(),
        "state": state,
        "detail": st.get("shortDetail") if state == "in" else None,
        "link": next((l["href"] for l in e.get("links", []) if "summary" in l.get("rel", [])), None),
        "leaders": [],
    }
    for t in c["competitors"]:
        team = t["team"]
        recs = t.get("records") or []
        score = t.get("score")
        g[t["homeAway"]] = {
            "code": team.get("abbreviation"),
            "name": team.get("shortDisplayName") or team.get("name"),
            "full": team.get("displayName"),
            "crest": team.get("logo"),
            "score": int(score) if state != "pre" and score not in (None, "") else None,
            "record": recs[0].get("summary") if recs else None,
        }
        if t.get("winner"):
            g["winner"] = t["homeAway"]
        if state != "pre":
            for ld in t.get("leaders", []):
                if ld.get("name") == "points" and ld.get("leaders"):
                    top = ld["leaders"][0]
                    g["leaders"].append(
                        {
                            "team": team.get("abbreviation"),
                            "name": top["athlete"].get("shortName"),
                            "value": top.get("displayValue"),
                        }
                    )
    return g


def nba():
    today = datetime.now(EASTERN).date()
    rounds = []
    for day, label in ((today - timedelta(days=1), "Last night"), (today, "Tonight")):
        data = fetch_json(f"{ESPN_NBA}/scoreboard?dates={day:%Y%m%d}")
        games = sorted((_nba_game(e) for e in data.get("events", [])), key=lambda g: g["ts"])
        rounds.append({"key": day.isoformat(), "label": label, "games": games})
    # Before US games tip off, "today" is upcoming; once any is underway show it.
    today_games = rounds[1]["games"]
    default = rounds[1]["key"] if any(g["state"] != "pre" for g in today_games) or not rounds[0]["games"] else rounds[0]["key"]
    if not rounds[0]["games"]:
        rounds[0]["label"] = "Yesterday"

    standings = []
    try:
        data = fetch_json("https://site.api.espn.com/apis/v2/sports/basketball/nba/standings")
        for conf in data.get("children", []):
            rows = []
            for e in conf["standings"]["entries"]:
                stats = {s["name"]: s for s in e["stats"]}

                def val(k, default=None, stats=stats):
                    s = stats.get(k)
                    return s.get("value", default) if s else default

                def disp(k, stats=stats):
                    s = stats.get(k)
                    return s.get("displayValue") if s else None

                team = e["team"]
                rows.append(
                    {
                        "rank": int(val("playoffSeed", 99) or 99),
                        "name": team.get("shortDisplayName") or team.get("name"),
                        "full": team.get("displayName"),
                        "crest": (team.get("logos") or [{}])[0].get("href"),
                        "w": int(val("wins", 0)),
                        "l": int(val("losses", 0)),
                        "gb": disp("gamesBehind"),
                        "streak": disp("streak"),
                        "diff": round(val("differential", 0) or 0, 1),
                    }
                )
            rows.sort(key=lambda r: r["rank"])
            label = conf.get("name", "").replace(" Conference", "")
            standings.append({"label": label, "rows": rows, "lines": [6, 10]})
    except Exception:  # noqa: BLE001
        pass
    return {"league": "nba", "rounds": rounds, "default": default, "standings": standings}


# ---------------------------------------------------------------- Greek league (ESAKE)

ESAKE = "https://www.esake.gr"

GBL_TEAMS = [
    ("ΠΑΝΑΘΗΝΑ", "Panathinaikos"),
    ("ΟΛΥΜΠΙΑΚ", "Olympiacos"),
    ("ΠΑΟΚ", "PAOK"),
    ("ΑΡΗΣ", "Aris"),
    ("ΑΕΚ", "AEK"),
    ("ΠΕΡΙΣΤΕΡΙ", "Peristeri"),
    ("ΠΡΟΜΗΘΕ", "Promitheas"),
    ("ΚΟΛΟΣΣΟΣ", "Kolossos Rhodes"),
    ("ΚΑΡΔΙΤΣΑ", "Karditsa"),
    ("ΜΑΡΟΥΣΙ", "Maroussi"),
    ("ΗΡΑΚΛΗΣ", "Iraklis"),
    ("ΜΥΚΟΝΟΣ", "Mykonos"),
    ("ΔΟΞΑ", "Doxa Lefkadas"),
    ("ΛΑΥΡΙΟ", "Lavrio"),
    ("ΑΠΟΛΛΩΝ", "Apollon Patras"),
    ("ΙΩΝΙΚΟΣ", "Ionikos"),
    ("ΚΗΦΙΣΙΑ", "Kifisia"),
    ("ΧΑΝΙΑ", "Chania"),
    ("VIKOS", "Vikos Falcons"),
    ("ΦALCONS", "Vikos Falcons"),
]

_GREEK_LATIN = str.maketrans(
    dict(zip("ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ", "A B G D E Z I Th I K L M N X O P R S T Y F Ch Ps O".split()))
)


def _strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def gbl_team_name(raw):
    s = _strip_accents(re.sub(r"\s+", " ", raw)).upper().strip()
    for key, name in GBL_TEAMS:
        if key in s:
            return name
    return s.translate(_GREEK_LATIN).title()


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


_MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def _esake_ts(text):
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})\w*\s*-\s*(\d{1,2}):(\d{2})", text)
    if not m:
        return None
    day, mon, hh, mm = int(m.group(1)), _MONTHS.get(m.group(2).lower()), int(m.group(3)), int(m.group(4))
    if not mon:
        return None
    start = season_start_year()
    year = start if mon >= 8 else start + 1
    return datetime(year, mon, day, hh, mm, tzinfo=ATHENS).timestamp()


def parse_esake_round(page):
    m = re.search(r"load\(function\(\)\{\s*\$j\('#series'\)\.val\('(\d+)'\)", page)
    rnd = int(m.group(1)) if m else None
    total = len(set(re.findall(r"#series'\)\.append\(new Option\('(\d+)'", page))) or 26
    games = []
    for block in page.split('<div class="esake-program-game">')[1:]:
        when = re.search(r'clock\.svg[^>]*>\s*([^<]+)<', block)
        tv = re.search(r'tv\.svg[^>]*>\s*([^<]+)<', block)
        gid = re.search(r"idgame=(\w+)&mode=3", block)
        sc = re.search(r'esake-program-game-final-score row equal">(.*?)</div>\s*</div>\s*</div>', block, re.S)
        if not sc:
            continue
        cols = re.split(r'<div class="col-[^"]*">', sc.group(1))[1:]
        if len(cols) < 3:
            continue

        def side(col):
            name = re.search(r"<span>(.*?)</span>", col, re.S)
            img = re.search(r'<img src="([^"]+)"', col)
            return {
                "name": gbl_team_name(_clean(name.group(1).replace("<br/>", " "))) if name else "?",
                "crest": ESAKE + img.group(1) if img else None,
            }

        home, away = side(cols[0]), side(cols[2])
        score = re.findall(r"\d+", _clean(cols[1]))
        state = "post" if len(score) == 2 else "pre"
        if state == "post":
            home["score"], away["score"] = int(score[0]), int(score[1])
        home["code"], away["code"] = home["name"], away["name"]
        g = {
            "id": gid.group(1) if gid else f"{rnd}-{len(games)}",
            "ts": _esake_ts(when.group(1)) if when else None,
            "state": state,
            "detail": None,
            "tv": tv.group(1).strip() if tv else None,
            "link": f"{ESAKE}/en/action/EsakegameView?idgame={gid.group(1)}&mode=3" if gid and state == "post" else None,
            "home": home,
            "away": away,
        }
        if state == "post":
            g["winner"] = "home" if home["score"] > away["score"] else "away"
        games.append(g)
    games.sort(key=lambda g: g["ts"] or 0)
    return rnd, total, games


def gbl_standings():
    page = fetch_text(f"{ESAKE}/en/action/EsakeRanking")
    body = page[page.find("<tbody>") : page.find("</tbody>")]
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 9:
            continue
        first = tds[0]
        img = re.search(r'<img src="([^"]+)"', first)
        name_html = first.split("</div>")[-1]
        pos = re.match(r"\s*(?:<a[^>]*>)?\s*(\d+)", first)
        wl = re.findall(r"\d+", tds[3])
        rows.append(
            {
                "rank": int(pos.group(1)) if pos else len(rows) + 1,
                "name": gbl_team_name(_clean(name_html)),
                "crest": ESAKE + img.group(1) if img else None,
                "pts": int(_clean(tds[1]) or 0),
                "gp": int(_clean(tds[2]) or 0),
                "w": int(wl[0]) if wl else 0,
                "l": int(wl[1]) if len(wl) > 1 else 0,
                "diff": int(re.sub(r"[^\d-]", "", _clean(tds[8])) or 0),
            }
        )
    return rows


def gbl():
    page = fetch_text(f"{ESAKE}/en/action/EsakeResults")
    rnd, total, games = parse_esake_round(page)
    rounds = {rnd: games}
    neighbour = rnd + 1 if all(g["state"] == "post" for g in games) else rnd - 1
    if 1 <= neighbour <= total:
        try:
            _, _, other = parse_esake_round(fetch_text(f"{ESAKE}/en/action/EsakeResults?series={neighbour:02d}"))
            rounds[neighbour] = other
        except Exception:  # noqa: BLE001
            pass
    ordered = sorted(rounds.items())
    try:
        standings = gbl_standings()
    except Exception:  # noqa: BLE001
        standings = []
    return {
        "league": "gbl",
        "rounds": [{"key": k, "label": f"Round {k}", "games": gs} for k, gs in ordered],
        "default": pick_default_round(ordered),
        "standings": [{"label": "Stoiximan GBL", "rows": standings, "lines": [8]}],
    }
