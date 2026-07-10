"""
test_workspace_cli.py - Unit tests for the workspace CLI ``--init`` flow.

Verifies that initializing a workspace creates the expected subdirectories
under ``.cobots/`` (``tasks/``, ``reports/``, ``knowledge/``, ``scratch/``),
writes the config file, and behaves idempotently when re-initialized.
"""

import importlib
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib and the CLI module are importable.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_CLI_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

# Patch venv activation before importing the CLI module.
sys.modules.setdefault("cobots_venv", MagicMock())
sys.modules.setdefault("cobots_venv.venv", MagicMock())

workspace_cli = importlib.import_module("workspace-cli")

from cobots_lib.workspace.constants import (
    CONFIG_FILE_NAME,
    KNOWLEDGE_DIR_NAME,
    REPORTS_DIR_NAME,
    SCRATCH_DIR_NAME,
    TASKS_DIR_NAME,
)


def _run_init(workspace_path: str, name: str = "") -> int:
    """Runs the CLI ``--init`` flow against an explicit workspace path.

    Patches ``sys.argv`` so ``main()`` parses the desired arguments, then
    returns the CLI's exit code.
    """
    argv = [
        "workspace-cli.py",
        "--init",
        "--workspace-path",
        workspace_path,
    ]
    if name:
        argv += ["--name", name]
    with patch.object(sys, "argv", argv):
        return workspace_cli.main()


# ---------------------------------------------------------------------------
# Tests: --init directory creation
# ---------------------------------------------------------------------------


class TestInitCreatesDirectories(unittest.TestCase):
    """Tests that ``--init`` creates all expected workspace subdirectories."""

    def test_init_creates_all_subdirectories(self) -> None:
        """A fresh init creates tasks/, reports/, knowledge/, and scratch/."""
        with tempfile.TemporaryDirectory() as tmp:
            working_dir = os.path.join(tmp, ".cobots")

            result = _run_init(working_dir)

            self.assertEqual(result, 0)
            self.assertTrue(os.path.isfile(
                os.path.join(working_dir, CONFIG_FILE_NAME)
            ))
            for sub in (
                TASKS_DIR_NAME,
                REPORTS_DIR_NAME,
                KNOWLEDGE_DIR_NAME,
                SCRATCH_DIR_NAME,
            ):
                self.assertTrue(
                    os.path.isdir(os.path.join(working_dir, sub)),
                    f"expected {sub}/ to be created",
                )

    def test_reinit_creates_missing_new_dirs_idempotently(self) -> None:
        """Re-initializing an older workspace adds knowledge/ and scratch/.

        Simulates a workspace created before the knowledge base existed (only
        tasks/ and reports/ present) and asserts a re-init backfills the new
        directories without error.
        """
        with tempfile.TemporaryDirectory() as tmp:
            working_dir = os.path.join(tmp, ".cobots")

            # First init, then remove the newer dirs to mimic an old workspace.
            self.assertEqual(_run_init(working_dir), 0)
            os.rmdir(os.path.join(working_dir, KNOWLEDGE_DIR_NAME))
            os.rmdir(os.path.join(working_dir, SCRATCH_DIR_NAME))
            self.assertFalse(
                os.path.isdir(os.path.join(working_dir, KNOWLEDGE_DIR_NAME))
            )

            # Re-init should recreate them idempotently.
            result = _run_init(working_dir)

            self.assertEqual(result, 0)
            self.assertTrue(
                os.path.isdir(os.path.join(working_dir, KNOWLEDGE_DIR_NAME))
            )
            self.assertTrue(
                os.path.isdir(os.path.join(working_dir, SCRATCH_DIR_NAME))
            )

    def test_init_is_repeatable_without_error(self) -> None:
        """Calling init twice on the same path succeeds both times."""
        with tempfile.TemporaryDirectory() as tmp:
            working_dir = os.path.join(tmp, ".cobots")

            self.assertEqual(_run_init(working_dir), 0)
            self.assertEqual(_run_init(working_dir), 0)
            for sub in (
                TASKS_DIR_NAME,
                REPORTS_DIR_NAME,
                KNOWLEDGE_DIR_NAME,
                SCRATCH_DIR_NAME,
            ):
                self.assertTrue(
                    os.path.isdir(os.path.join(working_dir, sub))
                )


if __name__ == "__main__":
    unittest.main()
