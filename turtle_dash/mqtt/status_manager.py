import threading
from datetime import datetime, timedelta

class StatusManager:
    def __init__(self, default_timeout=None):
        """
        :param default_timeout: seconds or timedelta to treat data as stale by default
                                (used only if you call get_status without a timeout)
        """
        self._statuses = {}       # name -> {"value": ..., "last_updated": datetime}
        self.default_timeout = default_timeout
        self._lock = threading.Lock()

    def update_status(self, name, value):
        """
        Record a new status value under `name`, timestamped now.
        """
        with self._lock:
            self._statuses[name] = {
                "value": value,
                "last_updated": datetime.now()
            }

    def get_status(self, name, default=None, timeout=None, fallback_on_stale=False):
        """
        Retrieve the last known value for `name`.
        - If `name` was never set → return `default`.
        - If timeout is given OR default_timeout is set, AND fallback_on_stale=True,
          AND data is older than the timeout → return `default`.
        - Otherwise → return the stored value.
        """
        # Acquire the status entry under lock
        with self._lock:
            entry = self._statuses.get(name)
        if entry is None:
            return default

        value       = entry["value"]
        last_updated = entry["last_updated"]

        # Determine which timeout to use
        effective = timeout if timeout is not None else self.default_timeout
        if effective is not None and fallback_on_stale:
            # Convert numeric seconds to timedelta
            if isinstance(effective, (int, float)):
                effective = timedelta(seconds=effective)
            # If stale, return default
            if datetime.now() - last_updated > effective:
                return default

        # Otherwise, always return the last known value
        return value

    def get_last_update(self, name):
        """
        (Optional) Return the timestamp when `name` was last updated, or None.
        """
        with self._lock:
            entry = self._statuses.get(name)
        return entry["last_updated"] if entry else None

# Global instance
status = StatusManager()