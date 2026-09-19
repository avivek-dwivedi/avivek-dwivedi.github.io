"""FastAPI app entry point for the LLM API reliability lab.

Illustrative implementation — not production-ready.
"""
from fastapi import FastAPI

from gateway import Gateway
from providers.mock import MockProvider

app = FastAPI(title="LLM API Reliability Lab")

# Wire up a mock provider and gateway
provider = MockProvider.from_config("config/mock-provider.yaml")
gateway = Gateway(provider=provider)

app.post("/v1/completions")(gateway.handle_completion)
app.get("/v1/stream/{request_id}")(gateway.resume_stream)
app.get("/health")(gateway.health)