"""Market snapshot from CNBC's public quote service."""

from urllib.parse import quote

from .net import fetch_json

CNBC = (
    "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    "?symbols={}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1"
)


def quotes(symbols):
    if not symbols:
        return []
    labels = {s["symbol"]: s.get("label") for s in symbols}
    url = CNBC.format(quote("|".join(labels), safe=""))
    data = fetch_json(url)
    raw = data["FormattedQuoteResult"]["FormattedQuote"]
    if isinstance(raw, dict):
        raw = [raw]
    by_symbol = {q.get("symbol"): q for q in raw}
    out = []
    for sym in labels:
        q = by_symbol.get(sym)
        if not q or not q.get("last"):
            continue
        pct = q.get("change_pct") or ""
        out.append(
            {
                "symbol": sym,
                "label": labels[sym] or q.get("shortName") or sym,
                "last": q.get("last"),
                "change": q.get("change"),
                "pct": pct,
                "dir": "up" if pct.startswith("+") else "down" if pct.startswith("-") else "flat",
                "time": q.get("last_time"),
            }
        )
    return out
