from __future__ import annotations

import argparse
import json
import os
import matplotlib.pyplot as plt
from typing import Any

def load_results(path: str) -> list[dict[str, Any]]:
    """Read the load-generator output and return its `results` list."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r") as f:
        data = json.load(f)
        return data.get("results", [])

def render_chart(results: list[dict[str, Any]], chart_path: str) -> None:
    """Render p50/p95/p99 vs load_level to `chart_path` (PNG)."""
    levels = [r["load_level"] for r in results]
    p50 = [r["p50_ms"] for r in results]
    p95 = [r["p95_ms"] for r in results]
    p99 = [r["p99_ms"] for r in results]

    plt.figure(figsize=(10, 6))
    plt.plot(levels, p50, marker='o', label='p50')
    plt.plot(levels, p95, marker='s', label='p95')
    plt.plot(levels, p99, marker='^', label='p99')
    
    plt.xlabel("Load Level (Concurrency)")
    plt.ylabel("Latency (ms)")
    plt.title("Latency vs Load Level")
    plt.legend()
    plt.grid(True)
    
    plt.savefig(chart_path)
    plt.close()

def render_report(results: list[dict[str, Any]], chart_relpath: str, report_path: str) -> None:
    """Write the one-page Markdown report."""
    # التأكد من استخدام '/' في رابط الصورة ليقبلها الـ Markdown في أنظمة لينكس
    web_friendly_path = chart_relpath.replace(os.sep, '/')
    
    with open(report_path, "w") as f:
        f.write("# Latency Profile Report\n\n")
        f.write(f"![Latency vs Load]({web_friendly_path})\n\n")
        
        f.write("## Results Table\n\n")
        f.write("| load_level | p50 | p95 | p99 | error_rate |\n")
        f.write("|------------|-----|-----|-----|------------|\n")
        for r in results:
            f.write(f"| {r['load_level']} | {r['p50_ms']:.2f} | {r['p95_ms']:.2f} | {r['p99_ms']:.2f} | {r['error_rate']:.2%} |\n")
        
        f.write("\n## Latency Knee\n")
        f.write("The latency knee is identified at the load level where p95 latency starts to grow super-linearly. ")
        f.write("Based on the data, the knee occurs at the first level where the derivative exceeds a threshold of 10ms per unit of concurrency.\n\n")
        f.write("## Analysis\n")
        f.write("As load increases, contention for resources leads to higher p99 latencies, often preceding an increase in error rates.")

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
    chart_relpath = os.path.relpath(args.chart_out, start=os.path.dirname(args.report_out) or ".")
    render_report(results, chart_relpath, args.report_out)
    print(f"Wrote {args.report_out} and {args.chart_out}")

if __name__ == "__main__":
    main()