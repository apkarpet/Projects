import threading
import time
from config import log, SCHEDULER_INTERVAL_HOURS


class AutoRefresher:
    def __init__(self, collect_fn, refresh_fn, interval_hours=None):
        self.collect_fn = collect_fn
        self.refresh_fn = refresh_fn
        self.interval = (interval_hours or SCHEDULER_INTERVAL_HOURS) * 3600
        self._thread = None
        self._active = False

    def start(self):
        if self._active:
            return
        self._active = True
        # Daemon thread: klonaei automata otan kleinei to parathyro, xwris na xreiastei extra cleanup
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log("Scheduler", "Started", f"ananeosi ana {self.interval // 3600} wres")

    def stop(self):
        self._active = False
        log("Scheduler", "Stopped")

    def _loop(self):
        while self._active:
            time.sleep(self.interval)
            if self._active:
                log("Scheduler", "Running", "auto-refresh ksekina")
                from storage import save_courses
                courses = self.collect_fn()
                save_courses(courses)
                self.refresh_fn()
