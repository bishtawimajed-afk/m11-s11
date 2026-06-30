# Module 11 — Stretch (Tue, Honors Track): Synthetic Load Profiling

Author an `httpx`-based load generator that ramps concurrent requests against the M11-instrumented `api`, captures p50/p95/p99 latencies and error rate at each load level from `/metrics`, identifies the *latency knee*, and writes a one-page profile report with a matplotlib chart of latency-vs-load.

**Repo:** standalone template (`m11-s11`). Branch: `stretch-tue-load-profiling`.

**Honors Track** — eligibility: required M11 work complete + On Track/Advanced + consistent attendance. See `curriculum/_overview/honors-track.md`.

---

## What you ship

1. `load_generator.py` — concurrent `httpx` client that ramps over `--load-levels`, captures per-level latency samples, queries `/metrics` for error counts, and writes `latency_results.json`.
2. `report_writer.py` — reads `latency_results.json`, produces:
   - `latency-profile-report.md` (one-page narrative + per-load-level table with p50/p95/p99 + error rate)
   - `charts/latency-vs-load.png` (matplotlib chart referenced from the report)
3. A short paragraph in the report identifying the **latency knee** with quantitative justification (where p95's derivative crosses your documented threshold).

The autograder verifies file presence, the report table parses, and the chart image is referenced. The TA rubric (`grading-rubric.md`) grades load-generator design, knee identification, and report quality.

---

## Setup

Branch from the template:

```bash
git checkout -b stretch-tue-load-profiling
pip install -r requirements.txt
```

Bring up a target API. The simplest path is the **fixture API** shipped with this repo (a small FastAPI service that exposes `/predict` and `/metrics`, with an injectable latency floor):

```bash
python fixture_api.py            # listens on http://127.0.0.1:8001
```

Run the load generator against it:

```bash
python load_generator.py --base-url http://127.0.0.1:8001 \
    --load-levels 1,5,10,25,50 --requests-per-level 100 \
    --output latency_results.json
```

Then build the report:

```bash
python report_writer.py --input latency_results.json \
    --report-out latency-profile-report.md \
    --chart-out charts/latency-vs-load.png
```

Advanced (optional): point `--base-url` at your M11 Lab's `api` service running in the M11 stack instead of the fixture.

---

## Tests

```bash
pytest tests/ -v
```

The autograder gates:

- `load_generator.py` defines a callable that returns per-level latency samples + error counts.
- `report_writer.py` produces `latency-profile-report.md` from a fixture results file.
- The report contains a Markdown table whose columns include `load_level`, `p50`, `p95`, `p99`, `error_rate`.
- The report references a chart image that exists on disk.

---

## License

This repository is provided for educational use only. See [LICENSE](LICENSE) for terms.

You may clone and modify this repository for personal learning and practice, and reference code you wrote here in your professional portfolio. Redistribution outside this course is not permitted.
