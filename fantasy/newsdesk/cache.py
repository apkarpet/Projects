"""In-memory cache persisted to disk, with stale-while-revalidate.

Every value is stored as {"t": fetched_at, "v": value}. A request for an
expired entry that is still fairly recent gets the old value immediately while
a background thread refreshes it; anything older is refreshed synchronously.
If a refresh fails the last good value is served, so the site keeps working
offline or when a source is down.
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict

log = logging.getLogger("newsdesk")


class Cache:
    def __init__(self, path: str, stale_window: float = 4 * 3600):
        self.path = path
        self.stale_window = stale_window
        self.data: dict = {}
        self._locks = defaultdict(threading.Lock)
        self._mu = threading.Lock()
        self._save_timer = None
        self._load()

    def _load(self):
        try:
            with open(self.path) as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            self.data = {}

    def _save_soon(self):
        with self._mu:
            if self._save_timer is None:
                self._save_timer = threading.Timer(2.0, self._save)
                self._save_timer.daemon = True
                self._save_timer.start()

    def _save(self):
        with self._mu:
            self._save_timer = None
            snapshot = dict(self.data)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(snapshot, f)
            os.replace(tmp, self.path)
        except OSError as e:
            log.warning("cache save failed: %s", e)

    def _lock(self, key):
        with self._mu:
            return self._locks[key]

    def get(self, key, ttl, fn, force=False):
        """Return a cached value, computing it with fn() when needed.

        ttl may be a number of seconds or a callable taking the cached value
        (so live games can refresh faster than finished ones).
        """
        entry = self.data.get(key)
        now = time.time()
        if entry and not force:
            age = now - entry["t"]
            limit = ttl(entry["v"]) if callable(ttl) else ttl
            if age < limit:
                return entry["v"]
            if age < self.stale_window:
                self._refresh_background(key, fn)
                return entry["v"]
        return self._refresh(key, fn, now)

    def _refresh(self, key, fn, requested_at):
        with self._lock(key):
            entry = self.data.get(key)
            if entry and entry["t"] >= requested_at:
                return entry["v"]  # another thread refreshed while we waited
            try:
                value = fn()
            except Exception as e:  # noqa: BLE001 - any source failure falls back
                log.warning("refresh %s failed: %s", key, e)
                if entry:
                    return entry["v"]
                raise
            self.data[key] = {"t": time.time(), "v": value}
        self._save_soon()
        return value

    def _refresh_background(self, key, fn):
        if self._lock(key).locked():
            return
        threading.Thread(
            target=self._refresh, args=(key, fn, time.time()), daemon=True
        ).start()

    def fetched_at(self, key):
        entry = self.data.get(key)
        return entry["t"] if entry else None
