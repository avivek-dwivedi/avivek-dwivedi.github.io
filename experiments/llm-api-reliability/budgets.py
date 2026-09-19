"""RPM, TPM, and concurrency budgets.

Reference lab implementation — single-process. In a multi-instance gateway,
budgets need distributed coordination.
"""
import threading
from dataclasses import dataclass


@dataclass
class BudgetSnapshot:
    rpm_remaining: int
    tpm_remaining: int
    concurrency_in_use: int
    concurrency_max: int


class BudgetManager:
    def __init__(self, rpm: int, tpm: int, max_concurrency: int):
        self._rpm = rpm
        self._tpm = tpm
        self._max_concurrency = max_concurrency
        self._rpm_used = 0
        self._tpm_used = 0
        self._concurrency_in_use = 0
        self._lock = threading.Lock()

    def can_take_rpm(self, n: int) -> bool:
        with self._lock:
            return self._rpm_used + n <= self._rpm

    def can_take_tpm(self, n: int) -> bool:
        with self._lock:
            return self._tpm_used + n <= self._tpm

    def concurrency_available(self) -> bool:
        with self._lock:
            return self._concurrency_in_use < self._max_concurrency

    def take_rpm(self, n: int):
        with self._lock:
            self._rpm_used += n

    def take_tpm(self, n: int):
        with self._lock:
            self._tpm_used += n

    def acquire_concurrency(self):
        with self._lock:
            self._concurrency_in_use += 1

    def release_concurrency(self):
        with self._lock:
            self._concurrency_in_use = max(0, self._concurrency_in_use - 1)

    def reconcile(self, reservation, actual_tokens: int):
        """Release unused reservation back to TPM budget."""
        with self._lock:
            unused = max(0, reservation.reserved_tokens - actual_tokens)
            self._tpm_used = max(0, self._tpm_used - unused)

    def release(self, reservation):
        """Release a full reservation (on failure)."""
        with self._lock:
            self._rpm_used = max(0, self._rpm_used - 1)
            self._tpm_used = max(0, self._tpm_used - reservation.reserved_tokens)

    def snapshot(self) -> BudgetSnapshot:
        with self._lock:
            return BudgetSnapshot(
                rpm_remaining=self._rpm - self._rpm_used,
                tpm_remaining=self._tpm - self._tpm_used,
                concurrency_in_use=self._concurrency_in_use,
                concurrency_max=self._max_concurrency,
            )