"""Provider interface.

Reference lab implementation.
"""
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract provider interface."""

    name: str = "base"

    @abstractmethod
    async def complete(self, request: dict) -> dict:
        """Non-streaming completion."""
        ...

    @abstractmethod
    async def stream(self, request: dict):
        """Streaming completion. Yields chunks."""
        ...