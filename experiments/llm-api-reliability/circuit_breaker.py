"""Circuit breaker state machine.

Reference lab implementation.
"""
import time


class CircuitBreaker:
    """Scope to provider/model/region — not one global breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, provider_name: str, failure_threshold: int = 5, cooldown: float = 30.0):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.state = self.CLOSED
        self._failures = 0
        self._opened_at: float = 0.0

    def is_open(self) -> bool:
        if self.state == self.OPEN:
            if time.monotonic() - self._opened_at >= self.cooldown:
                self.state = self.HALF_OPEN
                return False
            return True
        return False

    def record_success(self):
        self._failures = 0
        self.state = self.CLOSED

    def record_failure(self):
        self._failures += 1
        if self.state == self.HALF_OPEN:
            self._open()
        elif self._failures >= self.failure_threshold:
            self._open()

    def _open(self):
        self.state = self.OPEN
        self._opened_at = time.monotonic()