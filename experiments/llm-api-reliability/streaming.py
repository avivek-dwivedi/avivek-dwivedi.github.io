"""Bounded streaming pipeline with persistence.

Reference lab implementation.
"""
import asyncio
from persistence import StreamStore


class StreamManager:
    """Manages bounded stream buffers and delivery resume."""

    def __init__(self, max_buffer: int = 32):
        self.store = StreamStore()
        self._max_buffer = max_buffer
        self._active: dict[str, asyncio.Queue] = {}

    async def start_stream(self, request_id: str, provider_stream):
        """Start a bounded stream from provider, persisting chunks."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_buffer)
        self._active[request_id] = queue
        self.store.set_status(request_id, "RUNNING")

        async def producer():
            seq = 0
            try:
                async for chunk in provider_stream:
                    seq += 1
                    self.store.append(request_id, seq, chunk)
                    await queue.put(chunk)
            except Exception:
                self.store.set_status(request_id, "FAILED")
                await queue.put(None)
                return
            self.store.set_status(request_id, "COMPLETED")
            await queue.put(None)

        asyncio.create_task(producer())
        return queue

    def resume(self, request_id: str, last_sequence: int = 0):
        """Replay persisted chunks after last_sequence."""
        chunks = self.store.get_after(request_id, last_sequence)
        status = self.store.get_status(request_id)
        return {"chunks": chunks, "status": status, "has_live_stream": request_id in self._active}