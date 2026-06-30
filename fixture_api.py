"""Tiny fixture API for local load-generator development.

Mirrors the M11-instrumented `api` surface enough to drive `load_generator.py`:
exposes `POST /predict` (returns a stub payload after a small simulated delay)
and `GET /metrics` (Prometheus text format with a request counter + error
counter and a latency histogram).

This is the minimal target your load generator can run against without
bringing up the full M11 Docker stack. The autograder uses it in CI.
"""

from __future__ import annotations

import asyncio
import os
import random
import time

from fastapi import FastAPI, Request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

app = FastAPI()

REQUESTS = Counter("requests_total", "Total /predict requests", ["status"])
LATENCY = Histogram(
    "request_latency_seconds",
    "Latency of /predict",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)


# Injectable latency floor (seconds). Defaults to 5 ms; override via the
# FIXTURE_LATENCY_FLOOR_S env var to profile knee-point shapes (e.g. 0.05,
# 0.1, 0.25 to push the p95 into different histogram buckets).
LATENCY_FLOOR_S = float(os.environ.get("FIXTURE_LATENCY_FLOOR_S", "0.005"))
LATENCY_JITTER_S = float(os.environ.get("FIXTURE_LATENCY_JITTER_S", "0.015"))


@app.post("/predict")
async def predict(_: Request) -> dict:
    start = time.perf_counter()
    # Simulated work — the floor + jitter are injectable via env vars so
    # the load profile can be reshaped without code changes.
    await asyncio.sleep(LATENCY_FLOOR_S + random.uniform(0, LATENCY_JITTER_S))
    status = "error" if random.random() < 0.01 else "ok"
    LATENCY.observe(time.perf_counter() - start)
    REQUESTS.labels(status=status).inc()
    if status == "error":
        return Response(status_code=500)
    return {"prediction": "stub", "score": round(random.random(), 3)}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
