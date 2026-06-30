"""Generate the latency-profile report + chart from `load_generator.py` output.

Reads `latency_results.json` (the structure written by load_generator.py),
renders a matplotlib chart of p50/p95/p99 vs load level, and emits a one-page
Markdown report containing the chart reference and a per-load-level table.

Honors Track — TODO implementations required. See README.md for the contract.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


def load_results(path: str) -> list[dict[str, Any]]:
    """Read the load-generator output and return its `results` list.

    TODO: implement. Handle a missing or malformed file with a clear error.
    """
    raise NotImplementedError("TODO: implement load_results()")


def render_chart(results: list[dict[str, Any]], chart_path: str) -> None:
    """Render p50/p95/p99 vs load_level to `chart_path` (PNG).

    TODO: implement.
    - x-axis = load_level; y-axis = latency_ms.
    - Plot three series (p50, p95, p99).
    - Label axes; include a legend; annotate the latency knee (your choice of
      criterion; document it in the report).
    """
    raise NotImplementedError("TODO: implement render_chart()")


def render_report(
    results: list[dict[str, Any]],
    chart_relpath: str,
    report_path: str,
) -> None:
    """Write the one-page Markdown report with table + chart reference.

    The report MUST include a Markdown table with columns:
        load_level | p50 | p95 | p99 | error_rate

    The report MUST embed the chart via `![...](chart_relpath)` so the
    autograder can confirm the chart file is referenced.

    TODO: implement.
    - Compose the table from `results`.
    - Add a section "Latency Knee" with your quantitative justification.
    - Add a brief analysis paragraph tying latency-vs-load to the `/metrics`
      error-rate signal.
    """
    raise NotImplementedError("TODO: implement render_report()")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="M11 Stretch-Tue report writer")
    p.add_argument("--input", default="latency_results.json")
    p.add_argument("--report-out", default="latency-profile-report.md")
    p.add_argument("--chart-out", default="charts/latency-vs-load.png")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    results = load_results(args.input)
    os.makedirs(os.path.dirname(args.chart_out) or ".", exist_ok=True)
    render_chart(results, args.chart_out)
    chart_relpath = os.path.relpath(
        args.chart_out, start=os.path.dirname(args.report_out) or "."
    )
    render_report(results, chart_relpath, args.report_out)
    print(f"Wrote {args.report_out} and {args.chart_out}")


if __name__ == "__main__":
    main()
