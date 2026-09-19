"""Deadline-aware retry with exponential backoff and full jitter.

Reference lab implementation.
"""
import asyncio
import random
import time

BACKOFF_BASE = 0.5
BACKOFF_CAP = 10.0
MAX_ATTEMPTS = 5


class DeadlineExceeded(Exception):
    pass


class RetryBudgetExceeded(Exception):
    pass


class RetryBudget:
    """Caps aggregate retry traffic, not just per-request retries."""

    def __init__(self, max_retries: int = 50):
        self._remaining = max_retries

    def allow(self) -> bool:
        if self._remaining <= 0:
            return False
        self._remaining -= 1
        return True


async def retry_with_deadline(func, deadline: float, retry_budget: RetryBudget | None = None):
    """Call func with deadline-aware retry and full jitter.

    func must be an awaitable callable.
    """
    for attempt in range(MAX_ATTEMPTS):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DeadlineExceeded()

        try:
            return await func()
        except Exception as exc:
            if not _is_retryable(exc):
                raise

            if retry_budget is not None and not retry_budget.allow():
                raise RetryBudgetExceeded() from exc

            max_sleep = min(BACKOFF_CAP, BACKOFF_BASE * (2 ** attempt))
            sleep = random.uniform(0, max_sleep)

            if sleep >= remaining:
                raise DeadlineExceeded()

            await asyncio.sleep(sleep)

    raise DeadlineExceeded()


def _is_retryable(exc) -> bool:
    """Classify whether an exception is retryable.

    This is a simplified taxonomy. Production systems should classify
    per-provider error codes, HTTP status, and error type.
    """
    # Non-retryable: auth, permission, malformed request
    if exc.__class__.__name__ in ("AuthError", "PermissionError", "BadRequestError"):
        return False
    # Retryable: provider 5xx, network, timeout
    return True