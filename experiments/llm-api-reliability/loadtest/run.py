"""Load test runner for the LLM API reliability lab.

Experiment harness — not production code.
"""
import asyncio
import httpx
import time
import statistics
import sys

BASE_URL = "http://127.0.0.1:8000"


async def send_request(client, request_data, results):
    start = time.perf_counter()
    try:
        resp = await client.post(f"{BASE_URL}/v1/completions", json=request_data)
        elapsed = time.perf_counter() - start
        results.append({
            "status": resp.status_code,
            "elapsed": elapsed,
            "response": resp.json(),
        })
    except Exception as exc:
        elapsed = time.perf_counter() - start
        results.append({"status": "error", "elapsed": elapsed, "error": str(exc)})


async def run_experiment(concurrency: int, num_requests: int, small_ratio: float = 0.8):
    """Run a load experiment with mixed request sizes."""
    results = []
    async with httpx.AsyncClient(timeout=60) as client:
        tasks = []
        for i in range(num_requests):
            if i / num_requests < small_ratio:
                req = {"input_tokens": 300, "max_output_tokens": 200, "deadline_seconds": 20}
            else:
                req = {"input_tokens": 12000, "max_output_tokens": 4000, "deadline_seconds": 30}
            tasks.append(send_request(client, req, results))

        # Run with limited concurrency
        sem = asyncio.Semaphore(concurrency)

        async def bounded(task):
            async with sem:
                return await task

        await asyncio.gather(*[bounded(t) for t in tasks])

    # Summary
    latencies = [r["elapsed"] for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]

    print(f"\n=== Concurrency {concurrency}, {num_requests} requests ===")
    print(f"Successful: {len(latencies)}")
    print(f"Errors/rejected: {len(errors)}")
    if latencies:
        print(f"p50 latency: {statistics.median(latencies):.3f}s")
        print(f"p95 latency: {statistics.quantiles(latencies, n=20)[18]:.3f}s" if len(latencies) > 20 else "p95: n/a")

    return results


if __name__ == "__main__":
    conc = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    asyncio.run(run_experiment(conc, n))