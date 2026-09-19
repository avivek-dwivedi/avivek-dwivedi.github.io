"""Durable stream record — in-memory reference implementation.

Reference lab implementation. Production systems should use PostgreSQL,
Redis Streams, or another durable store.
"""
from dataclasses import dataclass, field


@dataclass
class StreamChunk:
    sequence: int
    data: str


class StreamStore:
    """In-memory durable stream record.

    This is NOT durable across process restarts. It demonstrates the
    interface and recovery mechanism. Use PostgreSQL or Redis in production.
    """

    def __init__(self):
        self._chunks: dict[str, list[StreamChunk]] = {}
        self._status: dict[str, str] = {}

    def append(self, request_id: str, seq: int, data: str):
        if request_id not in self._chunks:
            self._chunks[request_id] = []
        self._chunks[request_id].append(StreamChunk(sequence=seq, data=data))

    def get_after(self, request_id: str, last_sequence: int) -> list[dict]:
        chunks = self._chunks.get(request_id, [])
        return [
            {"sequence": c.sequence, "data": c.data}
            for c in chunks
            if c.sequence > last_sequence
        ]

    def set_status(self, request_id: str, status: str):
        self._status[request_id] = status

    def get_status(self, request_id: str) -> str:
        return self._status.get(request_id, "UNKNOWN")