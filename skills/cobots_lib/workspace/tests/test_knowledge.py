"""
test_knowledge.py - Unit tests for the knowledge entry model and helpers.

Covers `KnowledgeEntry` parsing/round-trip and `searchable_text`, the
filesystem store helpers (`list_knowledge_files`, `load_all_entries`,
`find_knowledge_file`), and the pure query helpers
(`filter_by_tag_expression`, `filter_by_regex`, `query_entries`,
`tag_census`).
"""

import os
import re
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

from cobots_lib.workspace.constants import (
    KNOWLEDGE_DIR_NAME,
    KNOWLEDGE_FILE_SUFFIX,
)
from cobots_lib.workspace.knowledge import (
    KnowledgeEntry,
    filter_by_regex,
    filter_by_tag_expression,
    find_knowledge_file,
    get_knowledge_dir,
    list_knowledge_files,
    load_all_entries,
    query_entries,
    tag_census,
)
from cobots_lib.workspace.tags import MatchAll, parse_tag_expression


def _write_entry(
    directory: str,
    entry_id: str,
    title: str = "Title",
    author: str = "byteboy",
    tags: "list[str] | None" = None,
    body: str = "Body content.",
    created: str = "2026-01-01 00:00:00",
    updated: str = "2026-01-01 00:00:00",
) -> str:
    """Writes a knowledge entry file into *directory* and returns its path.

    A small test factory that renders a well-formed frontmatter block with an
    inline YAML tag list, matching the entry template.
    """
    if tags is None:
        tags = ["git"]
    tag_list = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
    content = (
        "---\n"
        f'id: "{entry_id}"\n'
        f'title: "{title}"\n'
        f'author: "{author}"\n'
        f'created_timestamp: "{created}"\n'
        f'updated_timestamp: "{updated}"\n'
        f"tags: {tag_list}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{body}\n"
    )
    path = os.path.join(directory, f"{entry_id}{KNOWLEDGE_FILE_SUFFIX}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def _make_entry(
    entry_id: str = "abc",
    title: str = "Title",
    tags: "list[str] | None" = None,
    body: str = "Body content.",
) -> KnowledgeEntry:
    """Builds an in-memory `KnowledgeEntry` for pure query-helper tests."""
    if tags is None:
        tags = ["git"]
    return KnowledgeEntry(
        id=entry_id,
        title=title,
        author="byteboy",
        created_timestamp="2026-01-01 00:00:00",
        updated_timestamp="2026-01-01 00:00:00",
        tags=list(tags),
        body=body,
        path=f"/tmp/{entry_id}{KNOWLEDGE_FILE_SUFFIX}",
    )


# ===================================================================
# KnowledgeEntry model
# ===================================================================


class TestKnowledgeEntryFromFile(unittest.TestCase):
    """Verify `KnowledgeEntry.from_file` parses frontmatter and body."""

    def test_parses_all_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_entry(
                tmp,
                "deadbeef",
                title="How Git Works",
                author="lorey",
                tags=["git", "vcs"],
                body="Some durable knowledge.",
            )
            entry = KnowledgeEntry.from_file(path)
            self.assertEqual(entry.id, "deadbeef")
            self.assertEqual(entry.title, "How Git Works")
            self.assertEqual(entry.author, "lorey")
            self.assertEqual(entry.tags, ["git", "vcs"])
            self.assertIn("Some durable knowledge.", entry.body)
            self.assertEqual(entry.path, os.path.abspath(path))

    def test_body_includes_h1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_entry(tmp, "aa", title="My Title", body="Prose.")
            entry = KnowledgeEntry.from_file(path)
            self.assertIn("# My Title", entry.body)
            self.assertIn("Prose.", entry.body)

    def test_string_tag_coerced_to_list(self) -> None:
        # A hand-edited file might store a single scalar tag.
        content = (
            "---\n"
            'id: "xx"\n'
            'title: "T"\n'
            'author: "a"\n'
            'created_timestamp: "2026-01-01 00:00:00"\n'
            'updated_timestamp: "2026-01-01 00:00:00"\n'
            "tags: git\n"
            "---\n\nBody\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "xx" + KNOWLEDGE_FILE_SUFFIX)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            entry = KnowledgeEntry.from_file(path)
            self.assertEqual(entry.tags, ["git"])

    def test_malformed_frontmatter_yields_empty_fields(self) -> None:
        # A file with no frontmatter delimiters should not crash.
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad" + KNOWLEDGE_FILE_SUFFIX)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("no frontmatter here")
            entry = KnowledgeEntry.from_file(path)
            self.assertEqual(entry.id, "")
            self.assertEqual(entry.tags, [])
            self.assertIn("no frontmatter here", entry.body)


class TestSearchableText(unittest.TestCase):
    """Verify `searchable_text` joins title and body."""

    def test_joins_title_and_body(self) -> None:
        entry = _make_entry(title="Alpha", body="Beta gamma.")
        self.assertEqual(entry.searchable_text(), "Alpha\nBeta gamma.")


# ===================================================================
# Store helpers
# ===================================================================


class TestStoreHelpers(unittest.TestCase):
    """Verify directory resolution, listing, and prefix lookup."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.workspace = self._tmp.name
        self.kdir = os.path.join(self.workspace, KNOWLEDGE_DIR_NAME)
        os.makedirs(self.kdir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_get_knowledge_dir(self) -> None:
        self.assertEqual(
            get_knowledge_dir(self.workspace),
            os.path.join(self.workspace, KNOWLEDGE_DIR_NAME),
        )

    def test_list_files_sorted(self) -> None:
        _write_entry(self.kdir, "cccc")
        _write_entry(self.kdir, "aaaa")
        _write_entry(self.kdir, "bbbb")
        files = list_knowledge_files(self.workspace)
        stems = [os.path.basename(p) for p in files]
        self.assertEqual(
            stems,
            [
                "aaaa" + KNOWLEDGE_FILE_SUFFIX,
                "bbbb" + KNOWLEDGE_FILE_SUFFIX,
                "cccc" + KNOWLEDGE_FILE_SUFFIX,
            ],
        )

    def test_list_files_empty_store(self) -> None:
        self.assertEqual(list_knowledge_files(self.workspace), [])

    def test_load_all_entries(self) -> None:
        _write_entry(self.kdir, "aaaa", title="First")
        _write_entry(self.kdir, "bbbb", title="Second")
        entries = load_all_entries(self.workspace)
        self.assertEqual(len(entries), 2)
        self.assertEqual([e.title for e in entries], ["First", "Second"])

    def test_find_exact_match(self) -> None:
        path = _write_entry(self.kdir, "abcd1234")
        self.assertEqual(
            find_knowledge_file("abcd1234", self.workspace), path
        )

    def test_find_unique_prefix(self) -> None:
        path = _write_entry(self.kdir, "abcd1234")
        _write_entry(self.kdir, "ef567890")
        self.assertEqual(find_knowledge_file("abcd", self.workspace), path)

    def test_find_ambiguous_prefix_returns_none(self) -> None:
        _write_entry(self.kdir, "abcd1111")
        _write_entry(self.kdir, "abcd2222")
        self.assertIsNone(find_knowledge_file("abcd", self.workspace))

    def test_find_not_found_returns_none(self) -> None:
        _write_entry(self.kdir, "abcd1234")
        self.assertIsNone(find_knowledge_file("zzzz", self.workspace))

    def test_find_rejects_traversal_ids(self) -> None:
        # Plant a victim file just outside the knowledge dir.
        victim = os.path.join(self.workspace, "victim" + KNOWLEDGE_FILE_SUFFIX)
        with open(victim, "w", encoding="utf-8") as fh:
            fh.write("---\nid: v\n---\nbody\n")
        # None of these traversal/absolute IDs may resolve to the victim.
        for bad in [
            "../victim",
            "../../victim",
            "..",
            os.path.join(self.workspace, "victim"),
        ]:
            self.assertIsNone(
                find_knowledge_file(bad, self.workspace),
                f"traversal ID {bad!r} was not rejected",
            )
        self.assertTrue(os.path.isfile(victim))

    def test_find_rejects_absolute_id(self) -> None:
        path = _write_entry(self.kdir, "abcd1234")
        # An absolute path that happens to point at a real entry is still
        # rejected: legitimate IDs are bare tokens, never absolute paths.
        abs_id = path.removesuffix(KNOWLEDGE_FILE_SUFFIX)
        self.assertIsNone(find_knowledge_file(abs_id, self.workspace))


# ===================================================================
# Query helpers (pure)
# ===================================================================


class TestFilterByTagExpression(unittest.TestCase):
    """Verify `filter_by_tag_expression` selects matching entries."""

    def setUp(self) -> None:
        self.e1 = _make_entry("e1", tags=["git", "c"])
        self.e2 = _make_entry("e2", tags=["git", "c", "rust"])
        self.e3 = _make_entry("e3", tags=["git", "python"])
        self.e4 = _make_entry("e4", tags=["python"])
        self.entries = [self.e1, self.e2, self.e3, self.e4]

    def test_or_expression(self) -> None:
        expr = parse_tag_expression("git or rust")
        result = filter_by_tag_expression(self.entries, expr)
        self.assertEqual(result, [self.e1, self.e2, self.e3])

    def test_implicit_and(self) -> None:
        expr = parse_tag_expression("git rust")
        result = filter_by_tag_expression(self.entries, expr)
        self.assertEqual(result, [self.e2])

    def test_not_expression(self) -> None:
        expr = parse_tag_expression("not git")
        result = filter_by_tag_expression(self.entries, expr)
        self.assertEqual(result, [self.e4])

    def test_match_all_returns_everything(self) -> None:
        result = filter_by_tag_expression(self.entries, MatchAll())
        self.assertEqual(result, self.entries)

    def test_zero_matches(self) -> None:
        expr = parse_tag_expression("nonexistent")
        self.assertEqual(filter_by_tag_expression(self.entries, expr), [])


class TestFilterByRegex(unittest.TestCase):
    """Verify `filter_by_regex` searches title and body."""

    def setUp(self) -> None:
        self.e1 = _make_entry("e1", title="Rebasing", body="git rebase docs")
        self.e2 = _make_entry("e2", title="Merging", body="git merge docs")
        self.entries = [self.e1, self.e2]

    def test_matches_body(self) -> None:
        pattern = re.compile("rebase")
        self.assertEqual(
            filter_by_regex(self.entries, pattern), [self.e1]
        )

    def test_matches_title(self) -> None:
        pattern = re.compile("Merging")
        self.assertEqual(
            filter_by_regex(self.entries, pattern), [self.e2]
        )

    def test_ignore_case_flag(self) -> None:
        pattern = re.compile("REBASE", re.IGNORECASE)
        self.assertEqual(
            filter_by_regex(self.entries, pattern), [self.e1]
        )

    def test_zero_matches(self) -> None:
        pattern = re.compile("nonexistent")
        self.assertEqual(filter_by_regex(self.entries, pattern), [])


class TestQueryEntries(unittest.TestCase):
    """Verify `query_entries` ANDs the tag and regex filters."""

    def setUp(self) -> None:
        self.e1 = _make_entry("e1", tags=["git"], body="rebase")
        self.e2 = _make_entry("e2", tags=["git"], body="merge")
        self.e3 = _make_entry("e3", tags=["python"], body="rebase")
        self.entries = [self.e1, self.e2, self.e3]

    def test_both_filters_anded(self) -> None:
        expr = parse_tag_expression("git")
        pattern = re.compile("rebase")
        self.assertEqual(
            query_entries(self.entries, expr, pattern), [self.e1]
        )

    def test_tag_only(self) -> None:
        expr = parse_tag_expression("git")
        self.assertEqual(
            query_entries(self.entries, expr, None), [self.e1, self.e2]
        )

    def test_regex_only(self) -> None:
        pattern = re.compile("rebase")
        self.assertEqual(
            query_entries(self.entries, None, pattern), [self.e1, self.e3]
        )

    def test_no_filters_returns_all(self) -> None:
        self.assertEqual(
            query_entries(self.entries, None, None), self.entries
        )

    def test_match_all_expr_is_noop(self) -> None:
        pattern = re.compile("rebase")
        self.assertEqual(
            query_entries(self.entries, MatchAll(), pattern),
            [self.e1, self.e3],
        )

    def test_zero_matches(self) -> None:
        expr = parse_tag_expression("python")
        pattern = re.compile("merge")
        self.assertEqual(query_entries(self.entries, expr, pattern), [])


class TestTagCensus(unittest.TestCase):
    """Verify `tag_census` counts and sorts tags."""

    def test_counts_and_sort_order(self) -> None:
        entries = [
            _make_entry("e1", tags=["git", "c"]),
            _make_entry("e2", tags=["git", "rust"]),
            _make_entry("e3", tags=["git", "python"]),
            _make_entry("e4", tags=["python"]),
        ]
        # git=3, python=2, c=1, rust=1 -> sorted count desc then tag asc.
        self.assertEqual(
            tag_census(entries),
            [("git", 3), ("python", 2), ("c", 1), ("rust", 1)],
        )

    def test_case_insensitive_grouping(self) -> None:
        entries = [
            _make_entry("e1", tags=["Git"]),
            _make_entry("e2", tags=["GIT"]),
            _make_entry("e3", tags=["git"]),
        ]
        self.assertEqual(tag_census(entries), [("git", 3)])

    def test_duplicate_tag_within_entry_counts_once(self) -> None:
        entries = [_make_entry("e1", tags=["git", "Git", "GIT"])]
        self.assertEqual(tag_census(entries), [("git", 1)])

    def test_empty_store(self) -> None:
        self.assertEqual(tag_census([]), [])


if __name__ == "__main__":
    unittest.main()
