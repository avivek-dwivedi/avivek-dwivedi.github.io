"""Capability-aware routing.

Reference lab implementation.
"""
from dataclasses import dataclass, field


@dataclass
class RouteRequirements:
    streaming: bool = False
    tools: bool = False
    structured_output: bool = False
    min_context: int = 0
    vision: bool = False
    region: str | None = None
    max_cost: float | None = None


@dataclass
class Candidate:
    name: str
    streaming: bool = False
    tools: bool = False
    structured_output: bool = False
    max_context: int = 8192
    vision: bool = False
    region: str = "us"
    cost_per_1k: float = 0.0
    healthy: bool = True


class Router:
    """Filters candidates by capability, then applies routing policy."""

    def __init__(self, candidates: list[Candidate]):
        self.candidates = candidates

    def select(self, req: RouteRequirements) -> Candidate | None:
        healthy = [c for c in self.candidates if c.healthy]
        capable = [
            c for c in healthy
            if c.streaming >= req.streaming
            and c.tools >= req.tools
            and c.structured_output >= req.structured_output
            and c.max_context >= req.min_context
            and c.vision >= req.vision
            and (req.region is None or c.region == req.region)
            and (req.max_cost is None or c.cost_per_1k <= req.max_cost)
        ]
        if not capable:
            return None
        # Routing policy: lowest cost among capable, healthy candidates.
        # Production policy may weight latency, region, load, etc.
        return min(capable, key=lambda c: c.cost_per_1k)