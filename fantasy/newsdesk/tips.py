"""Players that fantasy tip columns keep recommending.

Sources (2026-27): Eurohoops' weekly EuroLeague Fantasy column (read through
its public WordPress API, English edition only; the Greek one is a
translation) and FantasyEdgeIQ's round preview (value picks and must-starts;
its "traps" are kept as warnings, not tips). BasketNews, RotoWire and the
EuroLeague site publish no Fantasy Challenge tips this season.

Only what the writers say is read; nothing here feeds the projection model,
which has not been backtested with it."""

import html
import re
import time
from datetime import datetime

from .fantasy import _fold
from .net import fetch_json, fetch_text

EUROHOOPS_API = (
    "https://www.eurohoops.net/wp-json/wp/v2/posts"
    "?search=euroleague%20fantasy&per_page=30&_fields=id,date_gmt,link,title,content"
)
FEIQ = "https://www.fantasyedgeiq.com"

WINDOW_DAYS = 28  # about six rounds: older tips were about different prices and roles

# A sentence that pitches a player uses words like these.
_POSITIVE = re.compile(
    r"\b(credits?|recommend\w*|suggest\w*|options?|picks?|value|bargains?|enablers?|budget|affordable|worth|consider|"
    r"invest\w*|must-haves?|must-starts?|locked-in|lock in|trust|captain|bench|enter your team|keep an eye|we like|pair him|gamble|bet)\b"
)
# Words right next to a name that mean he is missing or let the writer down
# ("without both Theo Maledon and Facundo Campazzo", "Jean Montero could miss").
_NEG_BEFORE = re.compile(r"\b(without|absen\w*|injur\w*|sidelined|suspended|avoid|sell|fade|drop|trap|overpriced|disappoint\w*)\b")
_NEG_AFTER = re.compile(r"\b(out|miss\w*|unavailable|uncertain|doubtful|injur\w*|sidelined|suspend\w*|disappoint\w*|worst)\b")
_SUFFIX = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv)$", re.I)


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _norm(s):
    """Lower-case, accents folded, hyphens and apostrophes kept as word parts."""
    return re.sub(r"[^a-z0-9' -]+", " ", _fold(s).lower().replace("’", "'"))


def _sentences(text):
    return [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", text) if x.strip()]


class _Matcher:
    """Finds the site's players in free text: by full name (the first name
    only has to share its first letter, so 'Cody' finds 'Codi'), or by last
    name alone when no other player shares it."""

    def __init__(self, players):
        self.full, last_count, by_last = [], {}, {}
        for p in players:
            parts = _norm(_SUFFIX.sub("", p["name"])).split()
            if len(parts) < 2:
                continue
            first, last = parts[0], " ".join(parts[1:])
            rx = rf"(?<![\w'-])({re.escape(first[0])}[a-z'-]*)\.? {re.escape(last)}(?![\w-])"
            self.full.append((re.compile(rx), first, p))
            key = parts[-1]
            last_count[key] = last_count.get(key, 0) + 1
            by_last[key] = p
        self.last = {k: p for k, p in by_last.items() if last_count[k] == 1 and len(k) >= 4}
        self.last_rx = {id(p): re.compile(rf"(?<![\w'-]){re.escape(k)}(?![\w-])") for k, p in self.last.items()}

    def find(self, text, last_names=False, only=None):
        """[(player, normalised text, start, end)] for each mention. only:
        players already known to be in the article, who may then be found
        by last name alone."""
        t = _norm(text)
        cands = {}
        for rx, first, p in self.full:
            for m in rx.finditer(t):
                cands.setdefault((m.start(), m.end()), []).append((m.group(1) == first, p))
        out, spans = [], []
        for (a, b), cs in cands.items():
            exact = [p for ok, p in cs if ok]
            pick = exact if exact else [p for _, p in cs]
            if len(pick) == 1:  # 'D. Hall' could be Devon or Donta: skip it
                out.append((pick[0], t, a, b))
            spans.append((a, b))
        pool = []
        if last_names:
            pool = list(self.last.values())
        elif only:
            pool = [p for p in only if id(p) in self.last_rx]
        for p in pool:
            for m in self.last_rx[id(p)].finditer(t):
                if not any(a <= m.start() < b for a, b in spans):
                    out.append((p, t, m.start(), m.end()))
        return out


def _negative(t, start, end):
    before = " ".join(t[max(0, start - 80) : start].split()[-6:])
    after = " ".join(t[end : end + 60].split()[:6])
    return bool(_NEG_BEFORE.search(before) or _NEG_AFTER.search(after))


def eurohoops_articles():
    posts = fetch_json(EUROHOOPS_API, timeout=20)
    out = []
    for p in posts:
        title = _text(p["title"]["rendered"])
        if "/en/" not in p["link"] or "fantasy" not in title.lower():
            continue
        ts = datetime.fromisoformat(p["date_gmt"] + "+00:00").timestamp()
        out.append({"source": "Eurohoops", "title": title, "link": p["link"], "ts": ts, "html": p["content"]["rendered"]})
    return out


def feiq_preview():
    """The current FantasyEdgeIQ round preview, split into its tables."""
    home = fetch_text(f"{FEIQ}/euroleague", timeout=25)
    m = re.search(r'href="(/euroleague/round-(\d+)-preview/)"', home)
    if not m:
        return None
    page = fetch_text(FEIQ + m.group(1), timeout=25)
    sections = {}
    for head, body in re.findall(r"<h2[^>]*>(.*?)</h2>(.*?)(?=<h2|$)", page, re.S):
        names = [_text(a) for a in re.findall(r'<a href="/euroleague/players/[^"]*"[^>]*>(.*?)</a>', body, re.S)]
        sections[_text(head).lower()] = names
    date = re.search(r"\((\d{4}-\d{2}-\d{2})\)", page)
    ts = datetime.fromisoformat(date.group(1)).timestamp() if date else time.time()
    pick = lambda word: next((v for k, v in sections.items() if word in k), [])  # noqa: E731
    return {
        "source": "FantasyEdgeIQ",
        "title": f"Round {m.group(2)} preview",
        "link": FEIQ + m.group(1),
        "ts": ts,
        "value": pick("value picks"),
        "must": pick("must-start"),
        "traps": pick("trap"),
    }


def fetch_sources():
    """Raw articles, cached by the caller. Each source fails on its own."""
    out, errors = [], []
    try:
        out.extend(eurohoops_articles())
    except Exception as e:  # noqa: BLE001
        errors.append(f"Eurohoops: {e}")
    try:
        prev = feiq_preview()
        if prev:
            out.append(prev)
    except Exception as e:  # noqa: BLE001
        errors.append(f"FantasyEdgeIQ: {e}")
    return {"articles": out, "errors": errors, "fetched": time.time()}


def tally(sources, players, now=None):
    """{key|team: {"count", "headline", "items": [...], "warnings": [...]}}.

    count is the number of recent articles that recommend the player, so a
    player tipped every week stands out from a one-off mention."""
    now = now or time.time()
    match = _Matcher(players)
    pid = lambda p: f"{p['key']}|{p['team']}"  # noqa: E731
    out = {}

    def add(p, art, how, warning=False, quote=None):
        e = out.setdefault(pid(p), {"count": 0, "headline": 0, "items": [], "warnings": []})
        item = {"source": art["source"], "title": art["title"], "link": art["link"], "ts": art["ts"], "how": how}
        if quote and how != "headline":
            item["quote"] = quote if len(quote) <= 220 else quote[:217].rsplit(" ", 1)[0] + "…"
        if warning:
            e["warnings"].append(item)
            return
        e["count"] += 1
        e["headline"] += how == "headline"
        e["items"].append(item)

    for art in sorted(sources.get("articles", []), key=lambda a: -a["ts"]):
        if now - art["ts"] > WINDOW_DAYS * 86400:
            continue
        if art["source"] == "FantasyEdgeIQ":
            done = set()
            for label, names in (("must-start", art["must"]), ("value pick", art["value"])):
                for p, *_ in match.find(" , ".join(names)):
                    if pid(p) not in done:
                        done.add(pid(p))
                        add(p, art, label)
            for p, *_ in match.find(" , ".join(art["traps"])):
                add(p, art, "trap", warning=True)
            continue
        pid_of = {}
        for p, *_ in match.find(art["title"], last_names=True):
            pid_of[pid(p)] = (p, "headline", art["title"])
        body = _sentences(_text(art["html"]))
        present = {pid(p): p for p, *_ in match.find(" . ".join(body))} | {k: v[0] for k, v in pid_of.items()}
        for sent in body:
            pitched = bool(_POSITIVE.search(_norm(sent)))
            for p, t, a0, a1 in match.find(sent, only=list(present.values())):
                k = pid(p)
                if k in pid_of or _negative(t, a0, a1) or not pitched:
                    continue
                pid_of[k] = (p, "in the article", sent)
        for p, how, quote in pid_of.values():
            add(p, art, how, quote=quote)
    for e in out.values():
        # A headline pick counts double; 2+ is what the site highlights.
        e["score"] = e["count"] + e["headline"]
    return out


def used(sources, now=None):
    """The articles inside the window, newest first, for the source note."""
    now = now or time.time()
    arts = [a for a in sources.get("articles", []) if now - a["ts"] <= WINDOW_DAYS * 86400]
    return [{k: a[k] for k in ("source", "title", "link", "ts")} for a in sorted(arts, key=lambda a: -a["ts"])]
