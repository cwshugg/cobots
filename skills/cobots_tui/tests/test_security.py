"""
test_security.py - Unit tests for the security module.

Tests path validation, text sanitization, and editor validation.
"""

import os
import tempfile
import unittest

from security import (
    validate_path_within_workspace,
    sanitize_display_text,
    validate_editor,
)


class TestValidatePathWithinWorkspace(unittest.TestCase):
    """Tests for validate_path_within_workspace()."""

    def test_valid_path_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, ".cobots")
            os.makedirs(workspace)
            file_path = os.path.join(workspace, "tasks", "test.task.md")
            os.makedirs(os.path.dirname(file_path))
            with open(file_path, "w") as f:
                f.write("test")

            result = validate_path_within_workspace(file_path, workspace)
            self.assertEqual(result, os.path.realpath(file_path))

    def test_traversal_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, ".cobots")
            os.makedirs(workspace)
            # Path that escapes the workspace.
            bad_path = os.path.join(workspace, "..", "..", "etc", "passwd")
            with self.assertRaises(ValueError):
                validate_path_within_workspace(bad_path, workspace)

    def test_symlink_outside_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, "workspace")
            os.makedirs(workspace)
            outside = os.path.join(tmp, "outside.txt")
            with open(outside, "w") as f:
                f.write("secret")
            symlink = os.path.join(workspace, "link.txt")
            os.symlink(outside, symlink)

            with self.assertRaises(ValueError):
                validate_path_within_workspace(symlink, workspace)

    def test_prefix_attack_raises_value_error(self) -> None:
        """A path like /workspace-evil/foo should fail when workspace is /workspace."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, "workspace")
            os.makedirs(workspace)
            evil_dir = os.path.join(tmp, "workspace-evil")
            os.makedirs(evil_dir)
            evil_file = os.path.join(evil_dir, "foo.txt")
            with open(evil_file, "w") as f:
                f.write("evil")

            with self.assertRaises(ValueError):
                validate_path_within_workspace(evil_file, workspace)

    def test_workspace_root_itself_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = os.path.join(tmp, ".cobots")
            os.makedirs(workspace)
            result = validate_path_within_workspace(workspace, workspace)
            self.assertEqual(result, os.path.realpath(workspace))


class TestSanitizeDisplayText(unittest.TestCase):
    """Tests for sanitize_display_text()."""

    def test_escapes_rich_markup(self) -> None:
        result = sanitize_display_text("[bold]hello[/bold]")
        # The escaped form uses backslash before brackets.
        self.assertIn("\\[bold]", result)
        self.assertIn("\\[/bold]", result)

    def test_plain_text_unchanged(self) -> None:
        result = sanitize_display_text("plain text here")
        self.assertEqual(result, "plain text here")

    def test_empty_string(self) -> None:
        result = sanitize_display_text("")
        self.assertEqual(result, "")

    def test_angle_brackets_in_text(self) -> None:
        result = sanitize_display_text("[red]danger[/red]")
        self.assertIn("\\[red]", result)


class TestValidateEditor(unittest.TestCase):
    """Tests for validate_editor()."""

    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(validate_editor(""))

    def test_whitespace_only_returns_none(self) -> None:
        self.assertIsNone(validate_editor("   "))

    def test_nonexistent_command_returns_none(self) -> None:
        self.assertIsNone(validate_editor("nonexistent_editor_xyz_123"))

    def test_valid_command_returns_list(self) -> None:
        # 'python3' should exist in the test environment.
        result = validate_editor("python3")
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "python3")


if __name__ == "__main__":
    unittest.main()
