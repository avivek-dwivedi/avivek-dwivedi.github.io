"""Mock provider with configurable failure behavior.

Reference lab implementation. This is NOT an emulation of any specific
proprietary provider. It exists to test failure conditions without
burning real API quota.
"""
import asyncio
import random
import yaml

from base import BaseProvider


class ThrottledError(Exception):
    pass


class ProviderServerError(Exception):
    pass


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(
        self,
        rpm: int = 100,
        tpm: int = 100_000,
        latency_ms: tuple[int, int] = (200, 800),
        first_token_ms: tuple[int, int] = (100, 500),
        failure_rate: float = 0.05,
        throttle_rate: float = 0.05,
        stream_chunk_delay_ms: int = 40,
        stream_failure_after_chunks: int | None = None,
    ):
        self.rpm = rpm
        self.tpm = tpm
        self.latency_ms = latency_ms
        self.first_token_ms = first_token_ms
        self.failure_rate = failure_rate
        self.throttle_rate = throttle_rate
        self.stream_chunk_delay_ms = stream_chunk_delay_ms
        self.stream_failure_after_chunks = stream_failure_after_chunks

    @classmethod
    def from_config(cls, path: str) -> "MockProvider":
        with open(path) as f:
            cfg = yaml.safe_load(f)
        lat = cfg.get("latency_ms", {"min": 200, "max": 800})
        ft = cfg.get("first_token_ms", {"min": 100, "max": 500})
        return cls(
            rpm=cfg.get("rpm", 100),
            tpm=cfg.get("tpm", 100_000),
            latency_ms=(lat["min"], lat["max"]),
            first_token_ms=(ft["min"], ft["max"]),
            failure_rate=cfg.get("failure_rate", 0.05),
            throttle_rate=cfg.get("throttle_rate", 0.05),
            stream_chunk_delay_ms=cfg.get("stream_chunk_delay_ms", 40),
            stream_failure_after_chunks=cfg.get("stream_failure_after_chunks"),
        )

    def _maybe_fail(self):
        r = random.random()
        if r < self.throttle_rate:
            raise ThrottledError("429 throttled")
        if r < self.throttle_rate + self.failure_rate:
            raise ProviderServerError("500 internal error")

    async def complete(self, request: dict) -> dict:
        self._maybe_fail()
        delay = random.uniform(self.latency_ms[0], self.latency_ms[1]) / 1000
        await asyncio.sleep(delay)

        input_tokens = request.get("input_tokens", 100)
        output_tokens = request.get("max_output_tokens", 256)
        # Simulate actual output being shorter than max
        actual_output = random.randint(10, output_tokens)
        total = input_tokens + actual_output

        return {
            "text": f"Mock response ({actual_output} tokens)",
            "input_tokens": input_tokens,
            "output_tokens": actual_output,
            "total_tokens": total,
        }

    async def stream(self, request: dict):
        self._maybe_fail()
        ft_delay = random.uniform(self.first_token_ms[0], self.first_token_ms[1]) / 1000
        await asyncio.sleep(ft_delay)

        max_tokens = request.get("max_output_tokens", 64)
        chunk_delay = self.stream_chunk_delay_ms / 1000

        for i in range(max_tokens):
            if self.stream_failure_after_chunks is not None and i >= self.stream_failure_after_chunks:
                raise ProviderServerError("stream interrupted")
            yield f"chunk_{i} "
            await asyncio.sleep(chunk_delay)