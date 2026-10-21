"""Summarize progress and status for goal files."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

STALLED_AFTER_HOURS = 48
AT_RISK_WITHIN_DAYS = 7


def parse_datetime(value: str) -> datetime:
    """Parse an ISO date or timestamp and normalize it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_goal(path: Path) -> dict[str, Any]:
    """Load and validate one JSON-compatible YAML goal file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"goal must be an object: {path}")
    required = {"id", "title", "target", "current", "deadline", "log"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path} is missing fields: {', '.join(sorted(missing))}")
    if float(data["target"]) <= 0:
        raise ValueError(f"goal target must be positive: {path}")
    if not isinstance(data["log"], list):
        raise ValueError(f"goal log must be a list: {path}")
    return data


def load_goals(goals_dir: Path) -> list[dict[str, Any]]:
    """Load all YAML goal files in stable filename order."""
    if not goals_dir.is_dir():
        raise ValueError(f"goals directory does not exist: {goals_dir}")
    return [load_goal(path) for path in sorted(goals_dir.glob("*.yaml"), key=lambda item: item.name.casefold())]


def summarize_goal(goal: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Calculate progress, timing, and status for one goal."""
    now_utc = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    target = float(goal["target"])
    current = float(goal["current"])
    progress = max(0.0, current / target * 100.0)
    deadline = date.fromisoformat(str(goal["deadline"]))
    days_left = (deadline - now_utc.date()).days
    log = goal.get("log", [])
    last_entry = max((parse_datetime(str(item["date"])) for item in log), default=None)
    hours_since = None if last_entry is None else max(0.0, (now_utc - last_entry).total_seconds() / 3600.0)
    if current >= target:
        status = "DONE"
    elif hours_since is None or hours_since > STALLED_AFTER_HOURS:
        status = "STALLED"
    elif days_left <= AT_RISK_WITHIN_DAYS and progress < 50.0:
        status = "AT_RISK"
    else:
        status = "ON_TRACK"
    return {
        "id": str(goal["id"]),
        "title": str(goal["title"]),
        "current": current,
        "target": target,
        "progress": progress,
        "days_left": days_left,
        "hours_since": hours_since,
        "status": status,
    }


def render_digest(goals: list[dict[str, Any]], now: datetime) -> str:
    """Render a Markdown digest table and attention list."""
    summaries = [summarize_goal(goal, now) for goal in goals]
    lines = [
        "# Goal digest",
        "",
        f"Checked at: `{now.isoformat()}`",
        "",
        "| ID | Goal | Progress | Days to deadline | Hours since entry | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in summaries:
        hours = "—" if item["hours_since"] is None else f"{item['hours_since']:.1f}"
        progress = f"{item['progress']:.0f}% ({item['current']:g}/{item['target']:g})"
        lines.append(
            f"| `{item['id']}` | {item['title']} | {progress} | {item['days_left']} | {hours} | **{item['status']}** |"
        )
    lines.extend(["", "## Requires attention", ""])
    attention = [item for item in summaries if item["status"] in {"STALLED", "AT_RISK"}]
    if attention:
        lines.extend(f"- **{item['status']}** — `{item['id']}`: {item['title']} ({item['progress']:.0f}% complete)."
                     for item in attention)
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the goal status checker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goals-dir", type=Path, default=Path("goals"))
    parser.add_argument("--out", type=Path, default=Path("digest.md"))
    parser.add_argument("--now", help="optional ISO timestamp to freeze the clock")
    args = parser.parse_args(argv)
    now = parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    goals = load_goals(args.goals_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_digest(goals, now), encoding="utf-8")
    print(f"Wrote goal digest: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
