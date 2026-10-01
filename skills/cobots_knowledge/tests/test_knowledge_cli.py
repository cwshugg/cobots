"""
test_knowledge_cli.py - Unit tests for the knowledge base CLI.

Exercises every subcommand (``create``, ``list``, ``query``, ``get``,
``edit``, ``delete``, ``tags``) by invoking the ``cmd_*`` handlers directly
with crafted ``argparse.Namespace`` objects against a temporary workspace,
mirroring the reports/tasks CLI test pattern. Coverage includes the boolean
tag grammar via the CLI, the regex + tag AND-combination, tag lowercasing on
write, and the delete ``--force`` bypass.
"""

import argparse
import contextlib
import io
import os
import sys
import tempfile
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

knowledge_cli = importlib.import_module("knowledge-cli")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config():
    """Returns a minimal config object exposing ``knowledge_id_length``."""
    return argparse.Namespace(knowledge_id_length=16)


def _run(handler, args_ns, stdin_text=None):
    """Invokes a ``cmd_*`` handler, capturing stdout/stderr and exit code.

    Sets the CLI's module-level ``_WORKSPACE_PATH`` from the namespace exactly
    as ``main()`` does, so handlers resolve against the temporary workspace.
    Returns a tuple ``(exit_code, stdout, stderr)``.
    """
    knowledge_cli._WORKSPACE_PATH = args_ns.workspace_path
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        if stdin_text is not None:
            with patch("sys.stdin", io.StringIO(stdin_text)):
                code = handler(args_ns, _config())
        else:
            code = handler(args_ns, _config())
    return code, out.getvalue(), err.getvalue()


def _ns(command, workspace, **kwargs):
    """Builds an ``argparse.Namespace`` for a subcommand handler."""
    base = {"command": command, "workspace_path": workspace}
    base.update(kwargs)
    return argparse.Namespace(**base)


def _create_entry(workspace, title, author, tags, body="body text"):
    """Creates an entry via the CLI handler; returns its created file path."""
    args = _ns(
        "create",
        workspace,
        title=title,
        author=author,
        tags=tags,
        empty=False,
    )
    code, out, _ = _run(knowledge_cli.cmd_create, args, stdin_text=body)
    assert code == 0, f"create failed: {out}"
    return out.strip()


class _KBTestCase(unittest.TestCase):
    """Base test case providing a fresh temporary workspace per test."""

    def setUp(self) -> None:
        """Creates a temporary workspace directory for the test."""
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = self._tmp.name

    def tearDown(self) -> None:
        """Removes the temporary workspace directory."""
        self._tmp.cleanup()

    def _id_of(self, path: str) -> str:
        """Extracts the entry ID from a created file path."""
        return os.path.basename(path).removesuffix(".knowledge.md")


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate(_KBTestCase):
    """Tests for the ``create`` subcommand."""

    def test_happy_path_lowercases_tags(self) -> None:
        """Creates a file with frontmatter and lowercased tags.

        Frontmatter is serialized via the shared, YAML-safe ``write_entry_file``
        (block style), so tags render as a YAML block sequence and scalars are
        emitted by PyYAML rather than hand-quoted.
        """
        path = _create_entry(
            self.workspace, "API Guide", "Lorey", "Bearer AUTH http"
        )
        self.assertTrue(os.path.isfile(path))
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("- bearer", text)
        self.assertIn("- auth", text)
        self.assertIn("- http", text)
        self.assertIn("title: API Guide", text)
        self.assertIn("author: lorey", text)
        # The H1 title is retained in the body.
        self.assertIn("# API Guide", text)
        # Round-trips cleanly back into a well-formed entry.
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertEqual(entry.title, "API Guide")
        self.assertEqual(entry.author, "lorey")
        self.assertEqual(entry.tags, ["bearer", "auth", "http"])

    def test_invalid_tag_exits_2(self) -> None:
        """Rejects an invalid tag character with exit code 2."""
        args = _ns(
            "create",
            self.workspace,
            title="T",
            author="a",
            tags="ru$t",
            empty=False,
        )
        code, _, err = _run(knowledge_cli.cmd_create, args, stdin_text="b")
        self.assertEqual(code, 2)
        self.assertIn("invalid tags", err)

    def test_reserved_word_tag_exits_2(self) -> None:
        """Rejects a reserved word used as a tag name with exit code 2."""
        args = _ns(
            "create",
            self.workspace,
            title="T",
            author="a",
            tags="git and",
            empty=False,
        )
        code, _, _ = _run(knowledge_cli.cmd_create, args, stdin_text="b")
        self.assertEqual(code, 2)

    def test_empty_body_without_empty_flag_exits_1(self) -> None:
        """Errors with exit 1 when STDIN body is empty and no --empty."""
        args = _ns(
            "create",
            self.workspace,
            title="T",
            author="a",
            tags="git",
            empty=False,
        )
        code, _, err = _run(knowledge_cli.cmd_create, args, stdin_text="   ")
        self.assertEqual(code, 1)
        self.assertIn("STDIN", err)

    def test_empty_flag_creates_empty_body(self) -> None:
        """Creates an entry with an empty body when --empty is given."""
        args = _ns(
            "create",
            self.workspace,
            title="T",
            author="a",
            tags="git",
            empty=True,
        )
        code, out, _ = _run(knowledge_cli.cmd_create, args)
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(out.strip()))

    def test_body_with_own_h1_is_not_duplicated(self) -> None:
        """A piped body that already has its own H1 is not given a second one."""
        path = _create_entry(
            self.workspace,
            "My Title",
            "x",
            "git",
            body="# My Title\n\nsome content",
        )
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        # Exactly one H1 heading is present in the body.
        h1_lines = [
            line for line in entry.body.splitlines() if line.startswith("# ")
        ]
        self.assertEqual(h1_lines, ["# My Title"])

    def test_body_without_h1_gets_title_injected(self) -> None:
        """A piped body without an H1 receives the title as an H1 heading."""
        path = _create_entry(
            self.workspace, "My Title", "x", "git", body="just content"
        )
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertIn("# My Title", entry.body)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

class TestList(_KBTestCase):
    """Tests for the ``list`` subcommand."""

    def test_empty_store(self) -> None:
        """Reports no entries on an empty store."""
        args = _ns("list", self.workspace, tags=None, show_path=False)
        code, out, _ = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 0)
        self.assertIn("No knowledge entries found.", out)

    def test_populated_and_tag_filter(self) -> None:
        """Lists entries and applies a boolean tag-expression filter."""
        _create_entry(self.workspace, "A", "x", "git rust")
        _create_entry(self.workspace, "B", "x", "git c")
        _create_entry(self.workspace, "C", "x", "python")

        args = _ns("list", self.workspace, tags=None, show_path=False)
        code, out, _ = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 3)

        # Filter reuses the shared expression engine.
        args = _ns(
            "list", self.workspace, tags="git and !rust", show_path=False
        )
        code, out, _ = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 0)
        self.assertIn("#git #c", out)
        self.assertNotIn("#rust", out)

    def test_filter_no_matches(self) -> None:
        """Prints the no-match message when a filter excludes everything."""
        _create_entry(self.workspace, "A", "x", "python")
        args = _ns("list", self.workspace, tags="rust", show_path=False)
        code, out, _ = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 0)
        self.assertIn("No matching knowledge entries.", out)

    def test_invalid_expression_exits_2(self) -> None:
        """Rejects a malformed tag expression with exit code 2."""
        _create_entry(self.workspace, "A", "x", "git")
        args = _ns(
            "list", self.workspace, tags="git and (rust", show_path=False
        )
        code, _, err = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 2)
        self.assertIn("invalid tag expression", err)

    def test_show_path(self) -> None:
        """Appends the absolute path when --show-path is given."""
        path = _create_entry(self.workspace, "A", "x", "git")
        args = _ns("list", self.workspace, tags=None, show_path=True)
        code, out, _ = _run(knowledge_cli.cmd_list, args)
        self.assertEqual(code, 0)
        self.assertIn(path, out)


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------

class TestQuery(_KBTestCase):
    """Tests for the ``query`` subcommand."""

    def setUp(self) -> None:
        """Seeds a small corpus mirroring the design's worked examples."""
        super().setUp()
        _create_entry(self.workspace, "E1", "x", "git c", body="alpha")
        _create_entry(self.workspace, "E2", "x", "git c rust", body="Bearer")
        _create_entry(self.workspace, "E3", "x", "git python", body="beta")
        _create_entry(self.workspace, "E4", "x", "python", body="argparse")

    def _query(self, **kwargs):
        """Runs the query handler with sensible defaults for omitted flags."""
        defaults = {
            "tags": None,
            "regex": None,
            "ignore_case": False,
            "show_path": False,
        }
        defaults.update(kwargs)
        args = _ns("query", self.workspace, **defaults)
        return _run(knowledge_cli.cmd_query, args)

    def test_tags_or(self) -> None:
        """Evaluates an OR expression."""
        code, out, _ = self._query(tags="git or rust")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 3)

    def test_tags_grouping(self) -> None:
        """Evaluates a parenthesized AND/OR expression."""
        code, out, _ = self._query(tags="git and (rust or c)")
        titles = out
        self.assertEqual(code, 0)
        self.assertIn("E1", titles)
        self.assertIn("E2", titles)
        self.assertNotIn("E3", titles)

    def test_tags_implicit_and(self) -> None:
        """Treats adjacency as an implicit AND."""
        code, out, _ = self._query(tags="git rust")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn("E2", out)

    def test_tags_not_and_case_insensitive(self) -> None:
        """Honors negation and case-folding of operators and tags."""
        code, out, _ = self._query(tags="NOT Git")
        self.assertEqual(code, 0)
        self.assertIn("E4", out)
        self.assertNotIn("E1", out)

    def test_regex_only(self) -> None:
        """Matches a regex over title + body."""
        code, out, _ = self._query(regex="argparse")
        self.assertEqual(code, 0)
        self.assertIn("E4", out)
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_regex_ignore_case(self) -> None:
        """Applies IGNORECASE to the regex when requested."""
        code, out, _ = self._query(regex="bearer", ignore_case=True)
        self.assertEqual(code, 0)
        self.assertIn("E2", out)

    def test_tags_and_regex_are_anded(self) -> None:
        """Requires both the tag expression and the regex to match."""
        code, out, _ = self._query(tags="git and c", regex="Bearer")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 1)
        self.assertIn("E2", out)

        # Same tags but a regex that matches none -> zero results.
        code, out, _ = self._query(tags="git and c", regex="zzznope")
        self.assertEqual(code, 0)
        self.assertIn("No matching knowledge entries.", out)

    def test_invalid_regex_exits_2(self) -> None:
        """Rejects an invalid regex with exit code 2."""
        code, _, err = self._query(regex="(")
        self.assertEqual(code, 2)
        self.assertIn("invalid regex", err)

    def test_invalid_tag_expression_exits_2(self) -> None:
        """Rejects a malformed tag expression with exit code 2."""
        for bad in ["git and", "or c", "git and ()", "git , c"]:
            code, _, err = self._query(tags=bad)
            self.assertEqual(code, 2, f"expected exit 2 for {bad!r}")
            self.assertIn("invalid tag expression", err)

    def test_no_filters_returns_all(self) -> None:
        """Returns all entries when neither filter is provided."""
        code, out, _ = self._query()
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 4)


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

class TestGet(_KBTestCase):
    """Tests for the ``get`` subcommand."""

    def test_found_by_prefix(self) -> None:
        """Retrieves an entry by a unique ID prefix."""
        path = _create_entry(self.workspace, "Title", "auth", "git c")
        entry_id = self._id_of(path)
        args = _ns("get", self.workspace, id=entry_id[:6])
        code, out, _ = _run(knowledge_cli.cmd_get, args)
        self.assertEqual(code, 0)
        self.assertIn("Title:          Title", out)
        self.assertIn("Tags:           git, c", out)

    def test_not_found_exits_1(self) -> None:
        """Errors with exit 1 for a missing ID."""
        args = _ns("get", self.workspace, id="deadbeef")
        code, _, err = _run(knowledge_cli.cmd_get, args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_ambiguous_prefix_exits_1(self) -> None:
        """Errors with exit 1 for an ambiguous prefix."""
        # Force a collision by creating entries and querying an empty prefix.
        _create_entry(self.workspace, "A", "x", "git")
        _create_entry(self.workspace, "B", "x", "git")
        args = _ns("get", self.workspace, id="")
        code, _, err = _run(knowledge_cli.cmd_get, args)
        self.assertEqual(code, 1)
        self.assertIn("ambiguous", err)


# ---------------------------------------------------------------------------
# edit
# ---------------------------------------------------------------------------

class TestEdit(_KBTestCase):
    """Tests for the ``edit`` subcommand."""

    def _edit_ns(self, entry_id, **kwargs):
        """Builds an edit Namespace with all flags defaulted."""
        defaults = {
            "id": entry_id,
            "add_tags": None,
            "remove_tags": None,
            "set_tags": None,
            "title": None,
            "body": False,
        }
        defaults.update(kwargs)
        return _ns("edit", self.workspace, **defaults)

    def _read(self, path):
        """Reads a file's full text."""
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_add_and_remove_tags_lowercased(self) -> None:
        """Adds and removes tags, storing them lowercased."""
        path = _create_entry(self.workspace, "T", "x", "git rust")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, add_tags="API", remove_tags="rust")
        code, _, _ = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 0)
        text = self._read(path)
        self.assertIn("api", text)
        self.assertNotIn("rust", text)

    def test_set_tags_replaces(self) -> None:
        """Replaces the whole tag set with --set-tags."""
        path = _create_entry(self.workspace, "T", "x", "git rust")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, set_tags="Python cli")
        code, _, _ = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 0)
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertEqual(sorted(entry.tags), ["cli", "python"])

    def test_set_tags_with_add_is_error(self) -> None:
        """Rejects combining --set-tags with --add-tags (exit 2)."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, set_tags="a", add_tags="b")
        code, _, err = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 2)
        self.assertIn("cannot be combined", err)

    def test_leave_zero_tags_exits_2(self) -> None:
        """Rejects an edit that would leave zero tags (exit 2)."""
        path = _create_entry(self.workspace, "T", "x", "git rust")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, remove_tags="git rust")
        code, _, err = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 2)
        self.assertIn("at least one tag", err)

    def test_title_updates_frontmatter_and_h1(self) -> None:
        """Updating the title rewrites both the frontmatter and body H1."""
        path = _create_entry(self.workspace, "Old Title", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, title="New Title")
        code, _, _ = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 0)
        text = self._read(path)
        self.assertIn("title: New Title", text)
        self.assertIn("# New Title", text)
        self.assertNotIn("# Old Title", text)

    def test_body_replaces_from_stdin(self) -> None:
        """Replacing the body from STDIN updates the content."""
        path = _create_entry(
            self.workspace, "T", "x", "git", body="original body"
        )
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, body=True)
        code, _, _ = _run(
            knowledge_cli.cmd_edit, args, stdin_text="fresh content here"
        )
        self.assertEqual(code, 0)
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertIn("fresh content here", entry.body)
        self.assertNotIn("original body", entry.body)

    def test_body_replace_without_h1_injects_title(self) -> None:
        """Replacing the body without an H1 injects the title as an H1."""
        path = _create_entry(self.workspace, "Doc Title", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, body=True)
        code, _, _ = _run(
            knowledge_cli.cmd_edit, args, stdin_text="body without heading"
        )
        self.assertEqual(code, 0)
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertIn("# Doc Title", entry.body)

    def test_body_replace_with_own_h1_is_not_duplicated(self) -> None:
        """Replacing the body with one that has its own H1 is not duplicated."""
        path = _create_entry(self.workspace, "Doc Title", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id, body=True)
        code, _, _ = _run(
            knowledge_cli.cmd_edit,
            args,
            stdin_text="# Custom Heading\n\nnew body",
        )
        self.assertEqual(code, 0)
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        h1_lines = [
            line for line in entry.body.splitlines() if line.startswith("# ")
        ]
        # Only the body's own H1 is present; the title is not injected again.
        self.assertEqual(h1_lines, ["# Custom Heading"])

    def test_updated_timestamp_refreshes(self) -> None:
        """An edit refreshes updated_timestamp while keeping created."""
        path = _create_entry(self.workspace, "T", "x", "git")
        before = knowledge_cli.KnowledgeEntry.from_file(path)
        entry_id = self._id_of(path)
        # Patch the timestamp helper so the change is observable.
        with patch.object(
            knowledge_cli, "_now_timestamp", return_value="2099-01-01 00:00:00"
        ):
            args = self._edit_ns(entry_id, add_tags="cli")
            code, _, _ = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 0)
        after = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertEqual(after.created_timestamp, before.created_timestamp)
        self.assertEqual(after.updated_timestamp, "2099-01-01 00:00:00")

    def test_no_flags_uses_editor(self) -> None:
        """Falls back to $EDITOR when no update flags are supplied."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id)
        fake = MagicMock(returncode=0)
        with patch.dict(os.environ, {"EDITOR": "true"}):
            with patch(
                "subprocess.run", return_value=fake
            ) as mock_run:
                code, _, _ = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 0)
        mock_run.assert_called_once()

    def test_no_flags_missing_editor_exits_1(self) -> None:
        """Errors with exit 1 when no flags and $EDITOR is unset."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = self._edit_ns(entry_id)
        env = os.environ.copy()
        env.pop("EDITOR", None)
        with patch.dict(os.environ, env, clear=True):
            code, _, err = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 1)
        self.assertIn("EDITOR", err)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete(_KBTestCase):
    """Tests for the ``delete`` subcommand."""

    def test_force_deletes_without_prompt(self) -> None:
        """Deletes without prompting when --force is passed."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = _ns("delete", self.workspace, id=entry_id, force=True, yes=False)
        code, out, _ = _run(knowledge_cli.cmd_delete, args)
        self.assertEqual(code, 0)
        self.assertIn("Deleted:", out)
        self.assertFalse(os.path.isfile(path))

    def test_declined_prompt_exits_1(self) -> None:
        """Keeps the file and exits 1 when the prompt is declined."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = _ns(
            "delete", self.workspace, id=entry_id, force=False, yes=False
        )
        code, _, _ = _run(knowledge_cli.cmd_delete, args, stdin_text="n\n")
        self.assertEqual(code, 1)
        self.assertTrue(os.path.isfile(path))

    def test_confirmed_prompt_deletes(self) -> None:
        """Deletes the file when the prompt is confirmed with 'y'."""
        path = _create_entry(self.workspace, "T", "x", "git")
        entry_id = self._id_of(path)
        args = _ns(
            "delete", self.workspace, id=entry_id, force=False, yes=False
        )
        code, _, _ = _run(knowledge_cli.cmd_delete, args, stdin_text="y\n")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.isfile(path))

    def test_missing_exits_1(self) -> None:
        """Errors with exit 1 for a missing ID."""
        args = _ns(
            "delete", self.workspace, id="deadbeef", force=True, yes=False
        )
        code, _, err = _run(knowledge_cli.cmd_delete, args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


# ---------------------------------------------------------------------------
# tags
# ---------------------------------------------------------------------------

class TestTags(_KBTestCase):
    """Tests for the ``tags`` subcommand."""

    def test_empty_store(self) -> None:
        """Reports no tags on an empty store."""
        args = _ns("tags", self.workspace, sort="count", json=False)
        code, out, _ = _run(knowledge_cli.cmd_tags, args)
        self.assertEqual(code, 0)
        self.assertIn("No tags found.", out)

    def test_census_counts_case_insensitive(self) -> None:
        """Counts tags case-insensitively, sorted by count desc."""
        _create_entry(self.workspace, "A", "x", "Git python")
        _create_entry(self.workspace, "B", "x", "git C")
        _create_entry(self.workspace, "C", "x", "GIT")
        args = _ns("tags", self.workspace, sort="count", json=False)
        code, out, _ = _run(knowledge_cli.cmd_tags, args)
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(lines[0].split(), ["TAG", "COUNT"])
        # git appears in all three entries (case-folded).
        self.assertEqual(lines[1].split(), ["git", "3"])

    def test_sort_name(self) -> None:
        """Sorts alphabetically when --sort name is given."""
        _create_entry(self.workspace, "A", "x", "zebra apple")
        args = _ns("tags", self.workspace, sort="name", json=False)
        code, out, _ = _run(knowledge_cli.cmd_tags, args)
        self.assertEqual(code, 0)
        lines = [l.split()[0] for l in out.strip().splitlines()[1:]]
        self.assertEqual(lines, ["apple", "zebra"])

    def test_json_output(self) -> None:
        """Emits parseable JSON when --json is given."""
        import json as _json

        _create_entry(self.workspace, "A", "x", "git python")
        args = _ns("tags", self.workspace, sort="count", json=True)
        code, out, _ = _run(knowledge_cli.cmd_tags, args)
        self.assertEqual(code, 0)
        data = _json.loads(out)
        tags = {item["tag"] for item in data}
        self.assertEqual(tags, {"git", "python"})

    def test_json_empty(self) -> None:
        """Emits an empty JSON array for an empty store."""
        import json as _json

        args = _ns("tags", self.workspace, sort="count", json=True)
        code, out, _ = _run(knowledge_cli.cmd_tags, args)
        self.assertEqual(code, 0)
        self.assertEqual(_json.loads(out), [])


# ---------------------------------------------------------------------------
# security: path traversal via --id (report 6378212b, finding 1)
# ---------------------------------------------------------------------------

class TestPathTraversal(_KBTestCase):
    """Traversal IDs must be rejected for get, edit, and delete alike."""

    def _plant_victim(self) -> str:
        """Creates a ``*.knowledge.md`` file *outside* the knowledge dir.

        Returns the victim path. A pre-fix exploit could read, overwrite, or
        delete this file via a crafted ``--id`` such as ``../victim``.
        """
        # Ensure the knowledge dir exists so resolution mirrors real usage.
        _create_entry(self.workspace, "seed", "x", "git")
        victim = os.path.join(self.workspace, "victim.knowledge.md")
        with open(victim, "w", encoding="utf-8") as fh:
            fh.write("---\nid: secret\n---\nTOP SECRET\n")
        return victim

    def test_get_rejects_traversal(self) -> None:
        """``get --id ../victim`` must not read outside the store."""
        self._plant_victim()
        args = _ns("get", self.workspace, id="../victim")
        code, out, err = _run(knowledge_cli.cmd_get, args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)
        self.assertNotIn("TOP SECRET", out)

    def test_delete_rejects_traversal(self) -> None:
        """``delete --id ../victim --force`` must not delete outside dir."""
        victim = self._plant_victim()
        args = _ns(
            "delete", self.workspace, id="../victim", force=True, yes=False
        )
        code, _, err = _run(knowledge_cli.cmd_delete, args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)
        self.assertTrue(
            os.path.isfile(victim), "traversal deleted an outside file!"
        )

    def test_delete_rejects_deep_traversal(self) -> None:
        """A multi-segment absolute-escape ID must also be rejected."""
        victim = self._plant_victim()
        # Point at the victim via an absolute path (with the suffix stripped,
        # since the resolver re-appends ``.knowledge.md``).
        abs_id = os.path.join(self.workspace, "victim")
        args = _ns(
            "delete", self.workspace, id=abs_id, force=True, yes=False
        )
        code, _, _ = _run(knowledge_cli.cmd_delete, args)
        self.assertEqual(code, 1)
        self.assertTrue(os.path.isfile(victim))

    def test_edit_rejects_traversal(self) -> None:
        """``edit --id ../victim`` must not overwrite outside the store."""
        victim = self._plant_victim()
        before = open(victim, encoding="utf-8").read()
        args = _ns(
            "edit",
            self.workspace,
            id="../victim",
            add_tags="pwned",
            remove_tags=None,
            set_tags=None,
            title=None,
            body=False,
        )
        code, _, err = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 1)
        self.assertIn("not found", err)
        self.assertEqual(open(victim, encoding="utf-8").read(), before)


# ---------------------------------------------------------------------------
# security: YAML frontmatter injection via --title (report 6378212b, #2)
# ---------------------------------------------------------------------------

class TestTitleYamlInjection(_KBTestCase):
    """A crafted --title must not forge or corrupt frontmatter keys."""

    def test_malicious_title_does_not_inject_keys(self) -> None:
        """A newline/quote-laden title stays a single ``title`` scalar."""
        evil = 'pwned"\ninjected_key: "value\nauthor: forged'
        path = _create_entry(self.workspace, evil, "realauthor", "git")

        # The entry round-trips with the literal title preserved and no
        # injected/forged keys.
        entry = knowledge_cli.KnowledgeEntry.from_file(path)
        self.assertEqual(entry.title, evil)
        self.assertEqual(entry.author, "realauthor")
        self.assertEqual(entry.tags, ["git"])

        # Parse the raw frontmatter and assert no injected key leaked in.
        frontmatter, _ = knowledge_cli.read_entry_file(path)
        self.assertNotIn("injected_key", frontmatter)
        self.assertEqual(
            set(frontmatter.keys()),
            {
                "id",
                "title",
                "author",
                "created_timestamp",
                "updated_timestamp",
                "tags",
            },
        )


# ---------------------------------------------------------------------------
# security: ReDoS guard on query --regex (report 6378212b, finding 3)
# ---------------------------------------------------------------------------

class TestQueryReDoS(_KBTestCase):
    """A catastrophic regex must time out cleanly instead of hanging."""

    def test_catastrophic_regex_times_out(self) -> None:
        """An evil pattern over modest content exits 2 within the budget."""
        # Content engineered to trigger catastrophic backtracking.
        _create_entry(
            self.workspace, "E", "x", "git", body="a" * 40 + "!"
        )
        args = _ns(
            "query",
            self.workspace,
            tags=None,
            regex=r"(a+)+$",
            ignore_case=False,
            show_path=False,
        )
        # Shrink the deadline so the test is fast but still proves the guard.
        with patch.object(
            knowledge_cli, "REGEX_MATCH_TIMEOUT_SECONDS", 0.5
        ):
            code, _, err = _run(knowledge_cli.cmd_query, args)
        self.assertEqual(code, 2)
        self.assertIn("timed out", err)


# ---------------------------------------------------------------------------
# security: edit read path handles malformed frontmatter (report #5)
# ---------------------------------------------------------------------------

class TestEditMalformedFrontmatter(_KBTestCase):
    """``edit`` on a corrupt entry must fail cleanly, not with a traceback."""

    def test_malformed_yaml_exits_2(self) -> None:
        """Invalid frontmatter YAML yields a clean exit-2 error."""
        path = _create_entry(self.workspace, "T", "x", "git")
        # Corrupt the frontmatter with unbalanced YAML flow syntax.
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("---\nid: [unclosed\ntitle: broken\n---\n\n# T\n\nbody\n")
        entry_id = self._id_of(path)
        args = _ns(
            "edit",
            self.workspace,
            id=entry_id,
            add_tags="cli",
            remove_tags=None,
            set_tags=None,
            title=None,
            body=False,
        )
        code, _, err = _run(knowledge_cli.cmd_edit, args)
        self.assertEqual(code, 2)
        self.assertIn("could not parse frontmatter", err)


if __name__ == "__main__":
    unittest.main()
