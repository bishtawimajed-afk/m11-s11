"""Synthetic load generator for the M11-instrumented `api`.

Ramps concurrent requests across a sequence of load levels, captures per-level
latency samples, and queries `/metrics` for error counts. Writes a structured
results JSON consumable by `report_writer.py`.

Honors Track — TODO implementations required. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import httpx
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass
class LoadLevelResult:
    """Per-load-level summary of one ramp step."""

    load_level: int
    requests_attempted: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float


def percentile(samples: list[float], q: float) -> float:
    """Return the q-th percentile (q in [0, 100]) of a samples list."""
    if not samples:
        return 0.0
    # Using statistics.quantiles as requested by the assignment
    # We use inclusive method for better precision
    try:
        # q-1 because quantiles returns a list of 99 cut points
        idx = max(0, min(int(q) - 1, 98))
        return statistics.quantiles(samples, n=100, method='inclusive')[idx]
    except Exception:
        # Fallback for very small sample sets
        sorted_samples = sorted(samples)
        k = (len(sorted_samples) - 1) * (q / 100.0)
        return sorted_samples[int(k)]


async def run_one_request(client: httpx.AsyncClient, base_url: str) -> tuple[float, bool]:
    """Issue one POST to {base_url}/predict and return (latency_ms, was_error)."""
    url = f"{base_url.rstrip('/')}/predict"
    start_time = time.perf_counter()
    was_error = False
    
    try:
        # Sending a simple payload as expected by the fixture
        response = await client.post(url, json={"data": [0.0]}, timeout=5.0)
        was_error = not response.is_success
    except (httpx.HTTPError, Exception):
        was_error = True
        
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    return latency_ms, was_error


async def run_level(
    base_url: str,
    concurrency: int,
    requests_per_level: int,
) -> LoadLevelResult:
    """Drive requests_per_level requests at concurrency in-flight."""
    semaphore = asyncio.Semaphore(concurrency)
    latency_samples = []
    error_count = 0

    async def worker(client: httpx.AsyncClient):
        nonlocal error_count
        async with semaphore:
            latency, was_error = await run_one_request(client, base_url)
            latency_samples.append(latency)
            if was_error:
                error_count += 1

    async with httpx.AsyncClient() as client:
        tasks = [worker(client) for _ in range(requests_per_level)]
        await asyncio.gather(*tasks)

    return LoadLevelResult(
        load_level=concurrency,
        requests_attempted=requests_per_level,
        p50_ms=percentile(latency_samples, 50),
        p95_ms=percentile(latency_samples, 95),
        p99_ms=percentile(latency_samples, 99),
        error_rate=error_count / requests_per_level if requests_per_level > 0 else 0.0,
    )


async def run_load_profile(
    base_url: str,
    load_levels: Iterable[int],
    requests_per_level: int,
) -> list[LoadLevelResult]:
    """Run each load level in sequence and return the aggregated results."""
    results = []
    for level in load_levels:
        print(f"Running level: {level} concurrent requests...")
        results.append(await run_level(base_url, level, requests_per_level))
    return results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="M11 Stretch-Tue load generator")
    p.add_argument("--base-url", required=True, help="Target API base URL")
    p.add_argument(
        "--load-levels",
        default="1,5,10,25,50",
        help="Comma-separated concurrency levels to ramp through",
    )
    p.add_argument("--requests-per-level", type=int, default=100)
    p.add_argument("--output", default="latency_results.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    levels = [int(x) for x in args.load_levels.split(",")]
    results = asyncio.run(
        run_load_profile(args.base_url, levels, args.requests_per_level)
    )
    with open(args.output, "w") as f:
        json.dump({"results": [asdict(r) for r in results]}, f, indent=2)
    print(f"Wrote {args.output} ({len(results)} levels)")


if __name__ == "__main__":
    main()