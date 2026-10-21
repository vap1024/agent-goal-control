"""Tests for goal status calculations and journal updates."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from add_entry import add_entry  # noqa: E402
from check_goals import render_digest, summarize_goal  # noqa: E402

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)


def goal(current: int, target: int, deadline: str, last: str | None) -> dict:
    """Build a compact synthetic goal for status tests."""
    return {
        "id": "goal-test",
        "title": "Synthetic test goal",
        "target": target,
        "current": current,
        "deadline": deadline,
        "log": [] if last is None else [{"date": last, "increase": 1, "text": "sample"}],
    }


class GoalControlTests(unittest.TestCase):
    """Verify status selection and persisted log updates."""

    def test_status_rules_with_frozen_time(self) -> None:
        self.assertEqual(summarize_goal(goal(10, 10, "2026-11-01", "2026-10-01T00:00:00Z"), NOW)["status"], "DONE")
        self.assertEqual(summarize_goal(goal(2, 10, "2026-11-01", "2026-10-18T00:00:00Z"), NOW)["status"], "STALLED")
        self.assertEqual(summarize_goal(goal(2, 10, "2026-10-23", "2026-10-21T08:00:00Z"), NOW)["status"], "AT_RISK")
        self.assertEqual(summarize_goal(goal(6, 10, "2026-10-23", "2026-10-21T08:00:00Z"), NOW)["status"], "ON_TRACK")

    def test_digest_contains_attention_items(self) -> None:
        digest = render_digest([goal(2, 10, "2026-10-23", "2026-10-21T08:00:00Z")], NOW)
        self.assertIn("**AT_RISK**", digest)
        self.assertIn("## Requires attention", digest)

    def test_add_entry_updates_current_and_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "goal-test.yaml"
            content = goal(2, 10, "2026-11-01", "2026-10-21T08:00:00Z")
            path.write_text(json.dumps(content), encoding="utf-8")
            result = add_entry(root, "goal-test", 1.5, "Added a sample milestone", NOW)
            updated = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(updated["current"], 3.5)
            self.assertEqual(len(updated["log"]), 2)
            self.assertEqual(updated["log"][-1]["text"], "Added a sample milestone")
            self.assertEqual(updated["log"][-1]["date"], "2026-10-21T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
