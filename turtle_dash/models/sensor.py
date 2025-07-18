import time

class Sensor:
    def __init__(self, name, default=0, valid_range=(None, None)):
        """
        :param name: Friendly name for debugging/logs
        :param default: Default value to fall back on (e.g., 0 or "N/A")
        :param valid_range: Tuple (min, max) or (None, None) for no limits
        """
        self.name = name
        self.value = default
        self.last_updated = 0
        self.default = default
        self.valid_range = valid_range

    def update(self, new_value):
        """Update the sensor value if valid, and record the timestamp."""
        if self.is_valid(new_value):
            self.value = new_value
            self.last_updated = time.time()
        else:
            print(f"[{self.name}] Invalid value received: {new_value}")

    def is_valid(self, value):
        """Check if the value falls within valid_range if defined."""
        min_val, max_val = self.valid_range
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    def is_stale(self, timeout=10):
        """Return True if the value hasn't updated within `timeout` seconds."""
        return (time.time() - self.last_updated) > timeout

    def get(self, timeout=None, fallback_on_stale=False):
        """
          Return the last known value.
        If timeout is given AND fallback_on_stale=True AND the data is stale,
        returns default instead of the stale value.
        """
        if timeout is not None and fallback_on_stale and self.is_stale(timeout):
            return self.default
        return self.value

    def reset_if_stale(self, timeout):
        """Reset the sensor to default if stale."""
        if self.is_stale(timeout):
            print(f"[{self.name}] Reset due to staleness.")
            self.value = self.default
            self.last_updated = time.time()

    def __repr__(self):
        return f"<Sensor {self.name}: {self.value} (updated {int(self.last_updated)})>"
