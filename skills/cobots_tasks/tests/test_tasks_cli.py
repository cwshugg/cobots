"""
test_tasks_cli.py - Unit tests for the tasks CLI edit subcommand.

Tests the ``edit`` subcommand: missing ``$EDITOR``, invalid task ID, and
successful launch of the editor via ``subprocess.run``.
"""

import argparse
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib and the CLI module are importable.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_CLI_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

# Patch venv activation before importing the CLI module.
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

import importlib
tasks_cli = importlib.import_module("tasks-cli")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_edit_args(**kwargs) -> argparse.Namespace:
    """Creates a Namespace mimicking parsed ``edit`` subcommand args."""
    defaults = {
        "command": "edit",
        "id": "abc123",
        "workspace_path": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests: cmd_edit
# ---------------------------------------------------------------------------


class TestCmdEdit(unittest.TestCase):
    """Tests for the ``cmd_edit`` command handler."""

    def test_missing_editor_env_var(self) -> None:
        """Returns 1 and prints an error when EDITOR is not set."""
        args = _make_edit_args()
        env = os.environ.copy()
        env.pop("EDITOR", None)

        with patch.dict(os.environ, env, clear=True):
            with patch("sys.stderr") as mock_stderr:
                result = tasks_cli.cmd_edit(args, config=None)

        self.assertEqual(result, 1)
        mock_stderr.write.assert_called()
        # Verify the error message content.
        written = "".join(
            call.args[0]
            for call in mock_stderr.write.call_args_list
            if call.args
        )
        self.assertIn("EDITOR environment variable is not set", written)

    def test_empty_editor_env_var(self) -> None:
        """Returns 1 when EDITOR is set to an empty string."""
        args = _make_edit_args()

        with patch.dict(os.environ, {"EDITOR": ""}, clear=True):
            with patch("sys.stderr") as mock_stderr:
                result = tasks_cli.cmd_edit(args, config=None)

        self.assertEqual(result, 1)
        written = "".join(
            call.args[0]
            for call in mock_stderr.write.call_args_list
            if call.args
        )
        self.assertIn("EDITOR environment variable is not set", written)

    @patch.object(tasks_cli, "resolve_task", return_value=None)
    def test_invalid_task_id(self, mock_resolve) -> None:
        """Returns 1 when the task ID cannot be resolved."""
        args = _make_edit_args(id="nonexistent")

        with patch.dict(os.environ, {"EDITOR": "vim"}):
            result = tasks_cli.cmd_edit(args, config=None)

        self.assertEqual(result, 1)
        mock_resolve.assert_called_once_with("nonexistent")

    @patch("subprocess.run")
    @patch.object(
        tasks_cli, "resolve_task",
        return_value="/fake/path/abc123.task.md",
    )
    def test_launches_editor_success(self, mock_resolve, mock_run) -> None:
        """Returns 0 when the editor exits successfully."""
        mock_run.return_value = MagicMock(returncode=0)
        args = _make_edit_args(id="abc123")

        with patch.dict(os.environ, {"EDITOR": "vim"}):
            result = tasks_cli.cmd_edit(args, config=None)

        self.assertEqual(result, 0)
        mock_resolve.assert_called_once_with("abc123")
        mock_run.assert_called_once_with(
            ["vim", "/fake/path/abc123.task.md"]
        )

    @patch("subprocess.run")
    @patch.object(
        tasks_cli, "resolve_task",
        return_value="/fake/path/abc123.task.md",
    )
    def test_launches_editor_failure(self, mock_resolve, mock_run) -> None:
        """Returns 1 when the editor exits with a non-zero code."""
        mock_run.return_value = MagicMock(returncode=1)
        args = _make_edit_args(id="abc123")

        with patch.dict(os.environ, {"EDITOR": "nano"}):
            result = tasks_cli.cmd_edit(args, config=None)

        self.assertEqual(result, 1)
        mock_run.assert_called_once_with(
            ["nano", "/fake/path/abc123.task.md"]
        )


if __name__ == "__main__":
    unittest.main()
