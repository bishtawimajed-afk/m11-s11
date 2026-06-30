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
    """Return the q-th percentile (q in [0, 100]) of a samples list.

    TODO: implement. Use a defensible method — e.g.,
    statistics.quantiles(samples, n=100, method='inclusive')[q - 1], or
    numpy.percentile. Document your choice in the report.
    """
    raise NotImplementedError("TODO: implement percentile()")


async def run_one_request(client, base_url: str) -> tuple[float, bool]:
    """Issue one request to `{base_url}/predict` and return (latency_ms, was_error).

    TODO: implement.
    - Send a POST with a small JSON body (any payload your fixture/API accepts).
    - Measure wall-clock latency in milliseconds.
    - Return was_error = True for non-2xx responses or transport exceptions.
    """
    raise NotImplementedError("TODO: implement run_one_request()")


async def run_level(
    base_url: str,
    concurrency: int,
    requests_per_level: int,
) -> LoadLevelResult:
    """Drive `requests_per_level` requests at `concurrency` in-flight.

    TODO: implement.
    - Use an asyncio.Semaphore or similar to bound in-flight to `concurrency`.
    - Collect latency samples; count errors.
    - Aggregate via percentile() and return a LoadLevelResult.
    """
    raise NotImplementedError("TODO: implement run_level()")


async def run_load_profile(
    base_url: str,
    load_levels: Iterable[int],
    requests_per_level: int,
) -> list[LoadLevelResult]:
    """Run each load level in sequence and return the aggregated results.

    TODO: implement.
    - For each level in load_levels, call run_level and append the result.
    - Return the ordered list.
    """
    raise NotImplementedError("TODO: implement run_load_profile()")


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
