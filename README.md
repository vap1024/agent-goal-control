# agent-goal-control

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Tests](https://img.shields.io/badge/tests-10%2F10%20passing-brightgreen)


A small standard-library tool for tracking goals alongside work with AI agents. A goal is a file, progress is a dated log, and a periodic or manual check creates a digest showing progress and stale goals. It runs locally and makes no network requests.

## Quick start

Requires Python 3.11 or newer. Goal files use JSON syntax, which is also valid YAML 1.2, so no YAML package is needed.

```console
python src/check_goals.py --goals-dir goals --out digest.md
python src/add_entry.py goal-demo-01 1 "Finished one synthetic milestone" --goals-dir goals
```

To schedule checks, invoke `check_goals.py` with your operating system's scheduler. The checker does not install or manage a scheduler for you. Use `--now 2026-10-21T12:00:00Z` for a reproducible run.

## Status rules

- `DONE`: current progress meets or exceeds the target.
- `STALLED`: the last log entry is more than 48 hours old, or no entry exists.
- `AT_RISK`: the deadline is within 7 days (including overdue) and progress is below 50%.
- `ON_TRACK`: none of the rules above apply.

The 7-day “close deadline” window is a documented default. Adjust the constant in `src/check_goals.py` if a different window fits your workflow.

## Example digest

See [`examples/digest_example.md`](examples/digest_example.md). The `goals/` directory contains three fictional goals and synthetic journal entries.

## Tests

The tests use `unittest` and are also collectable by pytest:

```console
python -m unittest discover -s tests -v
python -m pytest
```

Built with Codex, October 2026
