"""EuroLeague Fantasy helpers: BasketNews injury report, season PIR leaders
and top PIR performers per round (from official box scores)."""

import html
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from .net import fetch_json, fetch_text
from .sports import EL_FEEDS

BASKETNEWS = "https://basketnews.com"

SEVERITY = {
    "out": 0,
    "doubtful": 1,
    "uncertain": 2,
    "questionable": 2,
    "day-to-day": 2,
    "probable": 3,
    "expected": 3,
    "available": 3,
}


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _abs(url):
    if not url:
        return None
    return url if url.startswith("http") else BASKETNEWS + url


_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}


def _fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def player_key(name):
    """Loose identity for matching players across sources:
    'LAUVERGNE, JOFFREY' / 'Joffrey Lauvergne' / 'J. Lauvergne' -> 'lauvergne|j'."""
    name = _fold(_clean(name)).lower()
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
    else:
        parts = name.replace(".", ". ").split()
        if len(parts) < 2:
            return name
        first, last = parts[0], " ".join(parts[1:])
    tokens = [re.sub(r"[^a-z]", "", t) for t in last.split()]
    tokens = [t for t in tokens if t and t not in _SUFFIXES] or tokens
    return f"{tokens[-1] if tokens else ''}|{first[:1]}"


def _cap(word):
    up = word.upper()
    if up.rstrip(".") in ("II", "III", "IV"):
        return up
    if up.rstrip(".") in ("JR", "SR"):
        return up[0] + up[1:].lower().rstrip(".") + "."
    if len(word) <= 3 and not re.search(r"[AEIOUY]", up):
        return up  # TJ, CJ, DJ
    return re.sub(r"[^\W\d_]+", lambda m: m.group(0).capitalize(), word)


def pretty_name(raw):
    """'LAUVERGNE, JOFFREY' -> 'Joffrey Lauvergne', 'SHORTS, TJ' -> 'TJ Shorts'."""
    if "," in raw:
        last, first = [p.strip() for p in raw.split(",", 1)]
        raw = f"{first} {last}"
    return " ".join(_cap(w) if w.isupper() or w.islower() else w for w in raw.split())


def parse_injuries(page):
    start = page.find("injury_reports__head")
    if start < 0:
        raise ValueError("injury table not found")
    seg = page[start : page.find("</table>", start)]
    teams, cur = [], None
    for attrs, body in re.findall(r"<tr\b([^>]*)>(.*?)</tr>", seg, re.S):
        if "injury_reports__team-row" in attrs:
            name = re.search(r"<a[^>]*>(.*?)</a>", body, re.S)
            logo = re.search(r'<img src="([^"]+)"[^>]*injury_reports__team-logo', body)
            cur = {"team": _clean(name.group(1)) if name else "?", "logo": _abs(logo.group(1)) if logo else None, "players": []}
            teams.append(cur)
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", body, re.S)
        if cur is None or len(cells) < 5:
            continue
        pos, player, status, rnd, comment = cells[:5]
        plink = re.search(r'href="([^"]+)"', player)
        clink = re.search(r'href="([^"]+)"', comment)
        st = _clean(status)
        cur["players"].append(
            {
                "pos": _clean(pos),
                "name": _clean(player),
                "key": player_key(player),
                "link": _abs(plink.group(1)) if plink else None,
                "status": st,
                "severity": SEVERITY.get(st.lower(), 2),
                "round": _clean(rnd),
                "comment": _clean(comment),
                "comment_link": _abs(clink.group(1)) if clink else None,
            }
        )
    for t in teams:
        t["players"].sort(key=lambda p: p["severity"])
    m = re.search(r'"dateModified"\s*:\s*"\s*([^"]+)"', page)
    updated = None
    if m:
        try:
            updated = datetime.fromisoformat(m.group(1).strip()).timestamp()
        except ValueError:
            pass
    return {"teams": [t for t in teams if t["players"]], "updated": updated}


def injuries(url):
    try:
        page = fetch_text(url)
        if "injury_reports__head" not in page:
            raise ValueError("moved")
    except Exception:  # noqa: BLE001 - the article id changes between seasons
        home = fetch_text(BASKETNEWS)
        m = re.search(r'href="(/news-\d+-euroleague-injury-report[^"]*\.html)"', home)
        if not m:
            raise
        url = BASKETNEWS + m.group(1)
        page = fetch_text(url)
    data = parse_injuries(page)
    data["source"] = url
    return data


def pir_leaders(season, limit=25):
    data = fetch_json(
        f"{EL_FEEDS}/v3/competitions/E/statistics/players/traditional"
        f"?seasonMode=Single&seasonCode={season}&statisticMode=PerGame&limit=600"
    )
    players = data.get("players", [])
    if not players:
        return []
    max_gp = max(p.get("gamesPlayed", 0) for p in players)
    min_gp = max(1, round(max_gp * 0.5))
    rows = []
    for p in players:
        if p.get("gamesPlayed", 0) < min_gp:
            continue
        info = p["player"]
        rows.append(
            {
                "name": pretty_name(info["name"]),
                "key": player_key(info["name"]),
                "team": info["team"]["code"],
                "crest": info["team"].get("imageUrl"),
                "gp": int(p.get("gamesPlayed", 0)),
                "min": round(p.get("minutesPlayed", 0), 1),
                "pts": round(p.get("pointsScored", 0), 1),
                "reb": round(p.get("totalRebounds", 0), 1),
                "ast": round(p.get("assists", 0), 1),
                "pir": round(p.get("pir", 0), 1),
            }
        )
    rows.sort(key=lambda r: r["pir"], reverse=True)
    return rows[:limit]


def box_score(season, game):
    """Trimmed per-player lines for one finished game."""
    d = fetch_json(f"{EL_FEEDS}/v3/competitions/E/seasons/{season}/games/{game['id']}/stats")
    lines = []
    for side, team in (("local", game["home"]), ("road", game["away"])):
        for p in d.get(side, {}).get("players", []):
            s = p.get("stats") or {}
            if not s.get("timePlayed"):
                continue
            raw = p["player"]["person"]["name"]
            lines.append(
                {
                    "name": pretty_name(raw),
                    "key": player_key(raw),
                    "team": team["code"],
                    "crest": team.get("crest"),
                    "pos": POSITIONS.get((p["player"].get("positionName") or "").lower()),
                    "min": round(s.get("timePlayed", 0) / 60),
                    "secs": int(s.get("timePlayed", 0)),
                    "pts": int(s.get("points", 0)),
                    "reb": int(s.get("totalRebounds", 0)),
                    "ast": int(s.get("assistances", 0)),
                    "pir": int(s.get("valuation", 0)),
                    "fga": int(s.get("fieldGoalsAttempted2", 0) + s.get("fieldGoalsAttempted3", 0)),
                    "fta": int(s.get("freeThrowsAttempted", 0)),
                    "tov": int(s.get("turnovers", 0)),
                    "oreb": int(s.get("offensiveRebounds", 0)),
                    "stl": int(s.get("steals", 0)),
                    "blk": int(s.get("blocksFavour", 0)),
                    "pf": int(s.get("foulsCommited", 0)),
                    "fd": int(s.get("foulsReceived", 0)),
                    "start": bool(s.get("startFive")),
                }
            )
    return lines


POSITIONS = {"guard": "G", "forward": "F", "center": "C"}


_BOX_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="box")


def round_performers(season, rounds, cached_box, limit=15):
    """rounds: the EuroLeague payload's rounds. cached_box(season, game)
    returns box-score lines (finished games never change, so they are cached
    for good)."""
    out = []
    for r in rounds:
        done = [g for g in r["games"] if g["state"] == "post"]
        if not done:
            continue
        lines = []
        for res in _BOX_POOL.map(lambda g: _safe(cached_box, season, g), done):
            lines.extend(res)
        lines.sort(key=lambda p: p["pir"], reverse=True)
        out.append(
            {
                "key": r["key"],
                "label": r["label"],
                "played": len(done),
                "total": len(r["games"]),
                "players": lines[:limit],
            }
        )
    return out


def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001
        return []
