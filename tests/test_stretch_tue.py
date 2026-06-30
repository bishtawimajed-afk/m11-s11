"""Stretch-Tue 11 autograder — structural gate.

Per the rubric (`grading-rubric.md` lines 116-134), the autograder enforces
binary structural completeness; the TA rubric grades quality. These tests:

1. Verify the load generator and report writer modules import and expose the
   contracted entry points.
2. Verify `latency-profile-report.md` exists and contains a per-load-level
   table with the required columns.
3. Verify the chart image referenced by the report exists on disk.
4. Verify the load generator runs end-to-end against the fixture API.
"""

from __future__ import annotations

import importlib
import os
import re
import socket
import subprocess
import sys
import time

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------- structural --

def test_load_generator_module_present() -> None:
    mod = importlib.import_module("load_generator")
    for fn in ("run_one_request", "run_level", "run_load_profile", "percentile"):
        assert hasattr(mod, fn), f"load_generator must expose {fn}"


def test_report_writer_module_present() -> None:
    mod = importlib.import_module("report_writer")
    for fn in ("load_results", "render_chart", "render_report"):
        assert hasattr(mod, fn), f"report_writer must expose {fn}"


def test_report_exists_and_has_table() -> None:
    report = os.path.join(REPO_ROOT, "latency-profile-report.md")
    assert os.path.isfile(report), (
        "latency-profile-report.md must be generated and committed"
    )
    text = open(report).read()
    # Markdown table header with required columns (case-insensitive).
    header_re = re.compile(
        r"\|\s*load_level\s*\|\s*p50\s*\|\s*p95\s*\|\s*p99\s*\|\s*error_rate\s*\|",
        re.IGNORECASE,
    )
    assert header_re.search(text), (
        "report must contain a table with columns load_level | p50 | p95 | p99 | error_rate"
    )
    # At least one numeric data row beneath the header.
    data_rows = re.findall(r"^\|\s*\d+\s*\|", text, re.MULTILINE)
    assert len(data_rows) >= 1, "report table must have at least one data row"


def test_report_references_chart_image() -> None:
    report = os.path.join(REPO_ROOT, "latency-profile-report.md")
    text = open(report).read()
    img_re = re.compile(r"!\[[^\]]*\]\(([^)]+\.png)\)")
    m = img_re.search(text)
    assert m, "report must embed a chart image (![...](path.png))"
    chart_relpath = m.group(1)
    # Resolve relative to the report's directory.
    chart_path = os.path.normpath(os.path.join(REPO_ROOT, chart_relpath))
    assert os.path.isfile(chart_path), (
        f"chart image referenced by report does not exist: {chart_relpath}"
    )


# --------------------------------------------------------------- end-to-end --

def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise TimeoutError(f"{host}:{port} did not come up")


@pytest.fixture(scope="module")
def fixture_api():
    proc = subprocess.Popen(
        [sys.executable, "fixture_api.py"],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port("127.0.0.1", 8001)
        yield "http://127.0.0.1:8001"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_load_generator_runs_against_fixture(fixture_api, tmp_path) -> None:
    """End-to-end smoke: load generator completes against the fixture API."""
    out = tmp_path / "results.json"
    subprocess.run(
        [
            sys.executable,
            "load_generator.py",
            "--base-url",
            fixture_api,
            "--load-levels",
            "1,2",
            "--requests-per-level",
            "5",
            "--output",
            str(out),
        ],
        cwd=REPO_ROOT,
        check=True,
        timeout=60,
    )
    assert out.exists(), "load_generator did not write its output JSON"
    import json

    data = json.loads(out.read_text())
    assert "results" in data and len(data["results"]) == 2
    for r in data["results"]:
        for k in ("load_level", "p50_ms", "p95_ms", "p99_ms", "error_rate"):
            assert k in r, f"results entry missing key {k}"
        # Latency percentiles must be measured against the live fixture API,
        # which sleeps at least LATENCY_FLOOR_S (default 5 ms) per request.
        # An all-zero result indicates a learner stubbed the percentile
        # computation rather than measuring actual request latency.
        assert r["p50_ms"] > 0, (
            f"p50_ms is 0 at load_level={r['load_level']}; the fixture API "
            "introduces a >=5 ms latency floor so a real measurement is non-zero."
        )
        assert r["p95_ms"] >= r["p50_ms"], (
            f"p95_ms ({r['p95_ms']}) < p50_ms ({r['p50_ms']}); percentiles must be monotonic."
        )
        assert r["p99_ms"] >= r["p95_ms"], (
            f"p99_ms ({r['p99_ms']}) < p95_ms ({r['p95_ms']}); percentiles must be monotonic."
        )
        assert 0.0 <= r["error_rate"] <= 1.0, (
            f"error_rate ({r['error_rate']}) must be a fraction between 0.0 and 1.0."
        )
