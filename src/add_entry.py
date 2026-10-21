"""Append a progress entry to a goal file."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from check_goals import load_goal, parse_datetime


def add_entry(goals_dir: Path, goal_id: str, increase: float, text: str, now: datetime) -> Path:
    """Append a dated entry, update current progress, and return the goal path."""
    for path in sorted(goals_dir.glob("*.yaml"), key=lambda item: item.name.casefold()):
        goal = load_goal(path)
        if str(goal["id"]) != goal_id:
            continue
        now_utc = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
        date_text = now_utc.isoformat().replace("+00:00", "Z")
        goal["current"] = float(goal["current"]) + increase
        goal["log"].append({"date": date_text, "increase": increase, "text": text})
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(json.dumps(goal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path
    raise ValueError(f"goal id not found: {goal_id}")


def main(argv: list[str] | None = None) -> int:
    """Run the goal journal update command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("goal_id")
    parser.add_argument("increase", type=float)
    parser.add_argument("text")
    parser.add_argument("--goals-dir", type=Path, default=Path("goals"))
    parser.add_argument("--now", help="optional ISO timestamp to freeze the clock")
    args = parser.parse_args(argv)
    now = parse_datetime(args.now) if args.now else datetime.now(timezone.utc)
    try:
        path = add_entry(args.goals_dir, args.goal_id, args.increase, args.text, now)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f"Updated goal: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
