"""Small TTFT streaming client for an OpenAI-compatible endpoint.

Purpose: understand how TTFT is measured from a streaming response.
This is NOT the primary benchmark harness. For benchmarking, use the
official `vllm bench serve` tooling (see benchmark-load.sh).

Usage:
    MODEL_NAME=<model> python ttft_client.py
"""
import time

from openai import OpenAI

MODEL_NAME = "MODEL_NAME"
BASE_URL = "http://127.0.0.1:8000/v1"

client = OpenAI(base_url=BASE_URL, api_key="EMPTY")

prompt = "Explain KV cache in three sentences."
start = time.perf_counter()
first_token_time: float | None = None

stream = client.completions.create(
    model=MODEL_NAME,
    prompt=prompt,
    max_tokens=64,
    stream=True,
)

for chunk in stream:
    text = chunk.choices[0].text
    if text and first_token_time is None:
        first_token_time = time.perf_counter()
    print(text, end="", flush=True)

end = time.perf_counter()

print()
if first_token_time is not None:
    print(f"TTFT: {first_token_time - start:.4f}s")
else:
    print("TTFT: no tokens received")
print(f"End-to-end: {end - start:.4f}s")