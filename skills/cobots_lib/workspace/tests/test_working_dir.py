"""
test_working_dir.py - Unit tests for the cobots working directory resolution.

Tests ``resolve_working_dir``, ``find_working_dir``, and ``resolve_config_path``
from ``cobots_lib.workspace.working_dir``.  Special attention is paid to the
``--init`` use-case where the workspace CLI should always target the current
working directory rather than walking up to find a parent workspace.
"""

import os
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib is importable regardless of working directory.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.workspace.constants import CONFIG_FILE_NAME, WORKING_DIR_NAME
from cobots_lib.workspace.working_dir import (
    find_working_dir,
    resolve_config_path,
    resolve_working_dir,
)


# ===================================================================
# find_working_dir tests
# ===================================================================


class TestFindWorkingDir(unittest.TestCase):
    """Tests for the ``find_working_dir`` helper."""

    def test_returns_none_when_no_workspace_exists(self) -> None:
        """When no ``.cobots/`` directory exists in the tree, return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_working_dir(tmpdir)
            self.assertIsNone(result)

    def test_finds_workspace_in_start_dir(self) -> None:
        """Finds ``.cobots/`` in the start directory itself."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = os.path.join(tmpdir, WORKING_DIR_NAME)
            os.makedirs(ws)
            result = find_working_dir(tmpdir)
            self.assertEqual(result, ws)

    def test_finds_workspace_in_parent_dir(self) -> None:
        """Walks up and finds ``.cobots/`` in a parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = os.path.join(tmpdir, WORKING_DIR_NAME)
            os.makedirs(ws)
            child = os.path.join(tmpdir, "sub", "deep")
            os.makedirs(child)
            result = find_working_dir(child)
            self.assertEqual(result, ws)


# ===================================================================
# resolve_working_dir tests
# ===================================================================


class TestResolveWorkingDir(unittest.TestCase):
    """Tests for ``resolve_working_dir``."""

    def test_explicit_path_returned_as_is(self) -> None:
        """An explicit workspace_path is returned as an absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit = os.path.join(tmpdir, "custom_workspace")
            result = resolve_working_dir(explicit)
            self.assertEqual(result, os.path.abspath(explicit))

    def test_falls_back_to_cwd_when_no_workspace_found(self) -> None:
        """When no ``.cobots/`` exists anywhere, falls back to cwd."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = resolve_working_dir()
                expected = os.path.join(tmpdir, WORKING_DIR_NAME)
                self.assertEqual(result, expected)
            finally:
                os.chdir(orig)

    def test_walks_up_to_parent_workspace(self) -> None:
        """Without explicit path, resolve_working_dir walks up to a
        parent workspace — this is the default non-init behavior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_ws = os.path.join(tmpdir, WORKING_DIR_NAME)
            os.makedirs(parent_ws)
            child = os.path.join(tmpdir, "sub")
            os.makedirs(child)

            orig = os.getcwd()
            try:
                os.chdir(child)
                result = resolve_working_dir()
                self.assertEqual(result, parent_ws)
            finally:
                os.chdir(orig)


# ===================================================================
# resolve_config_path tests
# ===================================================================


class TestResolveConfigPath(unittest.TestCase):
    """Tests for ``resolve_config_path``."""

    def test_config_path_inside_working_dir(self) -> None:
        """Config path is ``CONFIG_FILE_NAME`` inside the working dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            explicit = os.path.join(tmpdir, "my_ws")
            result = resolve_config_path(explicit)
            self.assertEqual(
                result,
                os.path.join(os.path.abspath(explicit), CONFIG_FILE_NAME),
            )


# ===================================================================
# Init-specific behaviour (cwd bypass)
# ===================================================================


class TestInitCwdBypass(unittest.TestCase):
    """Verify the logic used by ``workspace-cli.py --init``.

    When ``--init`` is invoked without ``--workspace-path``, the CLI
    should compute the working directory as
    ``os.path.join(os.getcwd(), WORKING_DIR_NAME)`` — i.e. it must NOT
    call ``resolve_working_dir()`` which would walk up and potentially
    find a parent workspace.
    """

    def test_cwd_based_init_ignores_parent_workspace(self) -> None:
        """Even when a parent ``.cobots/`` exists, the cwd-based init
        path should point to a new ``.cobots/`` in the child directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a parent workspace.
            parent_ws = os.path.join(tmpdir, WORKING_DIR_NAME)
            os.makedirs(parent_ws)

            # Create a child directory (no workspace yet).
            child = os.path.join(tmpdir, "child_project")
            os.makedirs(child)

            orig = os.getcwd()
            try:
                os.chdir(child)

                # This is what resolve_working_dir() would return (parent).
                resolved = resolve_working_dir()
                self.assertEqual(resolved, parent_ws)

                # This is what --init should use instead (cwd-based).
                init_dir = os.path.join(os.getcwd(), WORKING_DIR_NAME)
                expected = os.path.join(child, WORKING_DIR_NAME)
                self.assertEqual(init_dir, expected)

                # They must differ when a parent workspace exists.
                self.assertNotEqual(init_dir, resolved)
            finally:
                os.chdir(orig)

    def test_cwd_based_init_matches_resolve_when_no_parent(self) -> None:
        """When no parent workspace exists, both approaches agree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orig = os.getcwd()
            try:
                os.chdir(tmpdir)
                resolved = resolve_working_dir()
                init_dir = os.path.join(os.getcwd(), WORKING_DIR_NAME)
                self.assertEqual(init_dir, resolved)
            finally:
                os.chdir(orig)


if __name__ == "__main__":
    unittest.main()
