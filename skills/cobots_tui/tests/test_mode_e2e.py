"""
test_mode_e2e.py - End-to-end tests for run_rich() and --show-overview.

Exercises the full wiring from workspace on disk through load_snapshot()
to the mode entry point, verifying output is produced correctly.
"""

import argparse
import io
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_SKILL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)

sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

from modes.rich_mode import run_rich
from config import load_status_config
from tests.helpers import (
    create_mock_workspace,
    write_task_file,
    write_report_file,
)


class TestShowOverviewEndToEnd(unittest.TestCase):
    """--show-overview produces non-empty Rich-formatted output."""

    def test_produces_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            reports_dir = os.path.join(ws, "reports")
            write_task_file(
                tasks_dir,
                task_id="e2e_task_0000001",
                title="E2E Task",
                status="underway",
                owner="bob",
            )
            write_report_file(
                reports_dir,
                report_id="e2e_report_00001",
                title="E2E Report",
            )

            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
                show_overview=True,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertTrue(
                len(output) > 0,
                "--show-overview produced no output",
            )

    def test_output_contains_task_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            write_task_file(
                tasks_dir,
                task_id="e2e_rich_00001",
                title="RichModeTask",
                status="done",
                owner="carol",
            )

            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
                show_overview=True,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertIn("RichModeTask", output)

    def test_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
                show_overview=True,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertTrue(len(output) > 0)
            self.assertIn("no recent activity", output)


class TestRunRichEndToEnd(unittest.TestCase):
    """run_rich() produces non-empty formatted output on a real workspace."""

    def test_produces_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            reports_dir = os.path.join(ws, "reports")
            write_task_file(
                tasks_dir,
                task_id="e2e_task_0000001",
                title="E2E Task",
                status="underway",
                owner="bob",
            )
            write_report_file(
                reports_dir,
                report_id="e2e_report_00001",
                title="E2E Report",
            )

            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertTrue(
                len(output) > 0, "run_rich() produced no output"
            )

    def test_output_contains_task_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            tasks_dir = os.path.join(ws, "tasks")
            write_task_file(
                tasks_dir,
                task_id="e2e_rich_00001",
                title="RichModeTask",
                status="done",
                owner="carol",
            )

            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertIn("RichModeTask", output)

    def test_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            status_config, cobots_config = load_status_config(ws)

            args = argparse.Namespace(
                workspace_path=ws,
                activity_count=20,
            )

            captured = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                sys.stdout = captured
                sys.stderr = io.StringIO()
                run_rich(
                    args,
                    status_config=status_config,
                    cobots_config=cobots_config,
                )
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            output = captured.getvalue()
            self.assertTrue(len(output) > 0)
            self.assertIn("no recent activity", output)


if __name__ == "__main__":
    unittest.main()
