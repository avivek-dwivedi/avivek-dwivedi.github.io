"""Gateway: admission, bounded queue, routing, stream management.

Reference lab implementation — demonstrates mechanisms, not a production server.
"""
import asyncio
import time

from admission import AdmissionController
from budgets import BudgetManager
from circuit_breaker import CircuitBreaker
from queueing import BoundedQueue
from retry import retry_with_deadline
from streaming import StreamManager


class Gateway:
    def __init__(self, provider, max_concurrency: int = 10, queue_size: int = 64):
        self.provider = provider
        self.budgets = BudgetManager(rpm=100, tpm=100_000, max_concurrency=max_concurrency)
        self.admission = AdmissionController(self.budgets)
        self.queue = BoundedQueue(maxsize=queue_size)
        self.breaker = CircuitBreaker(provider_name=provider.name)
        self.stream_manager = StreamManager()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def handle_completion(self, request: dict):
        """Handle a completion request with full admission + retry flow."""
        deadline = time.monotonic() + request.get("deadline_seconds", 30)

        # Estimate tokens
        input_tokens = request.get("input_tokens", 100)
        max_output = request.get("max_output_tokens", 256)

        # Admission
        reservation = self.admission.reserve(input_tokens, max_output)
        if reservation is None:
            return {"error": "admission_rejected", "reason": self.admission.last_reason}

        # Circuit breaker
        if self.breaker.is_open():
            return {"error": "circuit_open", "provider": self.provider.name}

        # Queue
        try:
            self.queue.enqueue(request)
        except asyncio.QueueFull:
            self.budgets.release(reservation)
            return {"error": "queue_full"}

        try:
            async with self._semaphore:
                result = await retry_with_deadline(
                    lambda: self.provider.complete(request),
                    deadline=deadline,
                )
            self.breaker.record_success()
            self.budgets.reconcile(reservation, actual_tokens=result.get("total_tokens", reservation.reserved_tokens))
            self.queue.dequeue()
            return result
        except Exception as exc:
            self.breaker.record_failure()
            self.queue.dequeue()
            self.budgets.release(reservation)
            return {"error": str(exc)}
        finally:
            pass

    async def resume_stream(self, request_id: str, last_sequence: int = 0):
        """Resume a stream from a given sequence number."""
        return self.stream_manager.resume(request_id, last_sequence)

    def health(self):
        return {
            "budgets": self.budgets.snapshot(),
            "queue_depth": self.queue.depth(),
            "breaker_state": self.breaker.state,
        }