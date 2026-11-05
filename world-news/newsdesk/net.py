"""Tiny HTTP client on top of urllib: browser-ish headers, gzip, sane timeouts."""

import gzip
import json
import re
import urllib.request
import zlib

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)


def fetch(url: str, timeout: float = 12) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        enc = (resp.headers.get("Content-Encoding") or "").lower()
    if enc == "gzip" or data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    elif enc == "deflate":
        data = zlib.decompress(data, -zlib.MAX_WBITS)
    return data


def fetch_text(url: str, timeout: float = 12) -> str:
    data = fetch(url, timeout)
    head = data[:300].decode("ascii", "ignore")
    m = re.search(r'encoding=["\']([\w-]+)', head)
    enc = m.group(1) if m else "utf-8"
    try:
        return data.decode(enc, "replace")
    except LookupError:
        return data.decode("utf-8", "replace")


def fetch_json(url: str, timeout: float = 12):
    return json.loads(fetch_text(url, timeout))
