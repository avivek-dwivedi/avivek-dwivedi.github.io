"""Bounded queue management.

Reference lab implementation.
"""
import asyncio


class BoundedQueue:
    def __init__(self, maxsize: int = 64):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)

    def enqueue(self, item):
        if self._queue.full():
            raise asyncio.QueueFull
        self._queue.put_nowait(item)

    def dequeue(self):
        return self._queue.get_nowait()

    def depth(self) -> int:
        return self._queue.qsize()

    def full(self) -> bool:
        return self._queue.full()