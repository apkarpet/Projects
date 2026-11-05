"""News feeds: fetch RSS / Atom / Google News / Hacker News / ESPN and merge
them into deduplicated, time-sorted topic lists."""

import hashlib
import html
import logging
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

from .net import fetch_json, fetch_text

log = logging.getLogger("newsdesk")

POOL = ThreadPoolExecutor(max_workers=24, thread_name_prefix="feed")

# ---------------------------------------------------------------- parsing


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    d = None
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError, IndexError):
        pass
    if d is None:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.timestamp()


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""


def _text(el):
    return "".join(el.itertext()).strip() if el is not None else ""


_XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}


def _fix_entities(text):
    """Make sloppy feeds parseable: HTML named entities and bare ampersands."""

    def named(m):
        name = m.group(1)
        if name in _XML_ENTITIES:
            return m.group(0)
        char = html.unescape(m.group(0))
        return char if char != m.group(0) else "&amp;" + name + ";"

    text = re.sub(r"&([A-Za-z][A-Za-z0-9]*);", named, text)
    return re.sub(r"&(?![A-Za-z][A-Za-z0-9]*;|#\d+;|#x[0-9A-Fa-f]+;)", "&amp;", text)


_BOILERPLATE = [
    r"The post .{0,300}? appeared first on .*$",
    r"\bContinue reading\b.*$",
    r"\bRead (the )?(full|more)\b.*$",
    r"\[(…|\.\.\.|&#8230;)\]\s*$",
]


def clean_summary(s, title="", limit=260):
    if not s:
        return ""
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"\s+", " ", html.unescape(s)).strip()
    for pat in _BOILERPLATE:
        s = re.sub(pat, "", s, flags=re.I).strip()
    if title and s.lower().startswith(title.lower()[:40]):
        return ""
    if len(s) > limit:
        cut = s[:limit].rsplit(" ", 1)[0].rstrip(",;:—-")
        s = cut + "…"
    return s


def _entry(el):
    d = {}
    for c in el:
        t = _local(c.tag)
        if t == "title":
            d.setdefault("title", _text(c))
        elif t == "link":
            href = c.get("href")
            if href:
                if c.get("rel", "alternate") == "alternate":
                    d.setdefault("link", href)
            elif c.text and c.text.strip():
                d.setdefault("link", c.text.strip())
        elif t in ("pubdate", "published", "updated", "date", "issued"):
            d.setdefault("date", c.text)
        elif t in ("description", "summary"):
            d.setdefault("summary", _text(c))
        elif t in ("encoded", "content"):
            d.setdefault("content", _text(c))
        elif t == "source":
            d.setdefault("source", _text(c))
        elif t == "comments":
            d.setdefault("comments", (c.text or "").strip())
    if "summary" not in d and "content" in d:
        d["summary"] = d["content"]
    return d


def parse_feed(text):
    """Return (channel_title, [raw entries])."""
    text = text.lstrip("﻿").strip()
    try:
        root = ET.fromstring(_fix_entities(text))
    except ET.ParseError:
        return None, _regex_entries(text)
    channel = None
    for el in root.iter():
        if _local(el.tag) == "title":
            channel = _text(el)
            break
    entries = [_entry(el) for el in root.iter() if _local(el.tag) in ("item", "entry")]
    return channel, entries


def _regex_entries(text):
    """Last-resort parser for feeds that are not well-formed XML."""
    out = []
    for block in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", text, re.S):

        def grab(tag):
            m = re.search(rf"<{tag}\b[^>]*>(.*?)</{tag}>", block, re.S)
            if not m:
                return ""
            v = m.group(1).strip()
            v = re.sub(r"^<!\[CDATA\[(.*)\]\]>$", r"\1", v, flags=re.S)
            return html.unescape(v)

        link = grab("link")
        if not link:
            m = re.search(r'<link\b[^>]*href="([^"]+)"', block)
            link = m.group(1) if m else ""
        out.append(
            {
                "title": re.sub(r"<[^>]+>", "", grab("title")),
                "link": link,
                "date": grab("pubDate") or grab("published") or grab("updated"),
                "summary": grab("description") or grab("summary"),
            }
        )
    return out


# ---------------------------------------------------------------- sources


def google_url(query, region="US"):
    region = region.upper()
    return (
        "https://news.google.com/rss/search?q="
        + quote_plus(query + " when:2d")
        + f"&hl=en-{region}&gl={region}&ceid={region}:en"
    )


def google_topic_url(topic, region="US"):
    region = region.upper()
    return (
        f"https://news.google.com/rss/headlines/section/topic/{topic.upper()}"
        f"?hl=en-{region}&gl={region}&ceid={region}:en"
    )


def norm_source(name):
    s = (name or "").lower().strip()
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"\.(com|net|org|co\.uk|gr)$", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def _item(title, link, ts, source, summary="", **extra):
    title = re.sub(r"\s+", " ", html.unescape(title or "")).strip()
    d = {
        "id": hashlib.sha1((link or title).encode()).hexdigest()[:12],
        "title": title,
        "link": link,
        "ts": ts,
        "source": source,
        "summary": summary,
    }
    d.update({k: v for k, v in extra.items() if v is not None})
    return d


def fetch_source(spec, source_lists=None):
    """Fetch one feed spec from config.json and return normalized items."""
    if "google" in spec or "google_topic" in spec:
        region = spec.get("region", "US")
        url = google_url(spec["google"], region) if "google" in spec else google_topic_url(spec["google_topic"], region)
        channel, entries = parse_feed(fetch_text(url))
        allowed = spec.get("sources")
        if isinstance(allowed, str):
            allowed = (source_lists or {}).get(allowed, [])
        allowed = {norm_source(a) for a in allowed} if allowed else None
        items = []
        for e in entries:
            title, source = e.get("title", ""), e.get("source") or "Google News"
            if source and title.endswith(" - " + source):
                title = title[: -len(source) - 3]
            if allowed is not None and norm_source(source) not in allowed:
                continue
            items.append(_item(title, e.get("link"), parse_date(e.get("date")), source))
        items.sort(key=lambda i: i["ts"] or 0, reverse=True)
        return items[: spec.get("max", 12)]

    if "hn_algolia" in spec:
        data = fetch_json(spec["hn_algolia"])
        items = []
        for h in data.get("hits", []):
            hn_url = f"https://news.ycombinator.com/item?id={h['objectID']}"
            items.append(
                _item(
                    h.get("title"),
                    h.get("url") or hn_url,
                    parse_date(h.get("created_at")),
                    spec.get("name", "Hacker News"),
                    points=h.get("points"),
                    comments=h.get("num_comments"),
                    comments_url=hn_url,
                )
            )
        return items

    if "espn" in spec:
        data = fetch_json(spec["espn"])
        items = []
        for a in data.get("articles", []):
            link = ((a.get("links") or {}).get("web") or {}).get("href")
            if not link or a.get("type") not in (None, "Story", "HeadlineNews", "Recap", "Preview"):
                continue
            items.append(
                _item(
                    a.get("headline"),
                    link,
                    parse_date(a.get("published")),
                    spec.get("name", "ESPN"),
                    clean_summary(a.get("description"), a.get("headline", "")),
                )
            )
        return items

    url = spec.get("rss") or spec.get("hn")
    channel, entries = parse_feed(fetch_text(url))
    name = spec.get("name") or channel or url
    items = []
    for e in entries:
        title = e.get("title", "")
        if "hn" in spec:
            raw = e.get("summary", "")
            pts = re.search(r"Points:\s*(\d+)", raw)
            com = re.search(r"#\s*Comments:\s*(\d+)", raw)
            items.append(
                _item(
                    title,
                    e.get("link"),
                    parse_date(e.get("date")),
                    name,
                    points=int(pts.group(1)) if pts else None,
                    comments=int(com.group(1)) if com else None,
                    comments_url=e.get("comments") or None,
                )
            )
        else:
            items.append(
                _item(title, e.get("link"), parse_date(e.get("date")), name, clean_summary(e.get("summary"), title))
            )
    if spec.get("match"):
        rx = re.compile(spec["match"])
        items = [i for i in items if rx.search(i["title"]) or rx.search(i["summary"] or "")]
    return items


# ---------------------------------------------------------------- merging


def _dedupe_key(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(words[:9])


def build_section(section, max_age_hours=72, source_lists=None, exclude=None):
    """Fetch every feed in a section concurrently and assemble its topics."""
    topics = section["topics"]
    exclude_rx = re.compile(exclude, re.I) if exclude else None
    jobs = []
    for t in topics:
        for spec in t["feeds"]:
            jobs.append((t["id"], spec, POOL.submit(fetch_source, spec, source_lists)))

    per_topic = {t["id"]: [] for t in topics}
    errors = []
    for tid, spec, fut in jobs:
        try:
            items = fut.result(timeout=25)
        except Exception as e:  # noqa: BLE001
            label = spec.get("name") or spec.get("google") or spec.get("rss")
            log.warning("feed %s failed: %s", label, e)
            errors.append(label)
            continue
        cap = spec.get("cap")
        for it in items:
            if cap:
                it["_cap"] = cap
        per_topic[tid].extend(items)

    cutoff = time.time() - max_age_hours * 3600
    seen = set()
    out = []
    for t in topics:
        limit = t.get("limit", 30)
        topic_rx = re.compile(t["exclude"], re.I) if t.get("exclude") else None
        items = [
            i
            for i in per_topic[t["id"]]
            if i["ts"] and i["ts"] >= cutoff and i["title"] and i["link"]
            and not (exclude_rx and exclude_rx.search(i["title"]))
            and not (topic_rx and topic_rx.search(i["title"]))
        ]
        if t.get("sort") == "points":
            items.sort(key=lambda i: i.get("points") or 0, reverse=True)
        else:
            items.sort(key=lambda i: i["ts"], reverse=True)
        picked, per_source = [], {}
        for it in items:
            key = _dedupe_key(it["title"])
            if key in seen:
                continue
            cap = it.pop("_cap", None) or 5
            n = per_source.get(it["source"], 0)
            if n >= cap:
                continue
            seen.add(key)
            per_source[it["source"]] = n + 1
            picked.append(it)
            if len(picked) >= limit:
                break
        for it in picked:
            it.pop("_cap", None)
        out.append(
            {
                "id": t["id"],
                "title": t["title"],
                "placement": t.get("placement", "main"),
                "items": picked,
            }
        )
    return {"topics": out, "errors": errors, "updated": time.time()}
