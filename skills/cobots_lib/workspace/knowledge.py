"""
knowledge.py - Knowledge entry model and store/query helpers.

Encapsulates the parsing, listing, lookup, and query filtering of knowledge
base entries so that the knowledge CLI stays thin. Entry files are markdown
with a YAML frontmatter block, stored under the ``knowledge`` subdirectory of
the cobots working directory.

This module reuses the shared workspace helpers rather than duplicating them:
`resolve_working_dir` for path resolution and
`cobots_lib.parsing.parse_frontmatter` for frontmatter parsing. Tag-expression
parsing and evaluation live in `cobots_lib.workspace.tags`.
"""

import glob
import os
import re
from dataclasses import dataclass, field

from cobots_lib.parsing import parse_frontmatter
from cobots_lib.workspace.constants import (
    KNOWLEDGE_DIR_NAME,
    KNOWLEDGE_FILE_SUFFIX,
)
from cobots_lib.workspace.tags import TagExpr, tag_expression_matches
from cobots_lib.workspace.working_dir import resolve_working_dir


@dataclass(frozen=True)
class KnowledgeEntry:
    """A single knowledge base entry parsed from disk.

    Holds the frontmatter fields, the free-form markdown body, and the
    absolute path to the source file.
    """

    id: str
    title: str
    author: str
    created_timestamp: str
    updated_timestamp: str
    tags: list[str] = field(default_factory=list)
    body: str = ""
    path: str = ""

    @classmethod
    def from_file(cls, path: str) -> "KnowledgeEntry":
        """Builds a `KnowledgeEntry` from a knowledge file on disk.

        Uses the shared `parse_frontmatter` helper. Missing frontmatter
        fields default to empty values, and the ``tags`` field is coerced to
        a list of strings so that callers always receive a well-formed entry
        even if a file was hand-edited.
        """
        frontmatter, body = parse_frontmatter(path)

        raw_tags = frontmatter.get("tags", [])
        if isinstance(raw_tags, str):
            tags = [raw_tags]
        elif isinstance(raw_tags, list):
            tags = [str(tag) for tag in raw_tags]
        else:
            tags = []

        return cls(
            id=str(frontmatter.get("id", "")),
            title=str(frontmatter.get("title", "")),
            author=str(frontmatter.get("author", "")),
            created_timestamp=str(frontmatter.get("created_timestamp", "")),
            updated_timestamp=str(frontmatter.get("updated_timestamp", "")),
            tags=tags,
            body=body,
            path=os.path.abspath(path),
        )

    def searchable_text(self) -> str:
        """Returns the text that regex queries search over.

        This is the title joined to the full body by a newline, so that a
        single regex can match content in either.
        """
        return f"{self.title}\n{self.body}"


# ---------------------------------------------------------------------------
# Store helpers (filesystem)
# ---------------------------------------------------------------------------

def get_knowledge_dir(workspace_path: str | None = None) -> str:
    """Returns the absolute path to the knowledge directory."""
    return os.path.join(
        resolve_working_dir(workspace_path), KNOWLEDGE_DIR_NAME
    )


def list_knowledge_files(workspace_path: str | None = None) -> list[str]:
    """Returns sorted absolute paths to all knowledge files in the store."""
    pattern = os.path.join(
        get_knowledge_dir(workspace_path), f"*{KNOWLEDGE_FILE_SUFFIX}"
    )
    return sorted(glob.glob(pattern))


def load_all_entries(
    workspace_path: str | None = None,
) -> list[KnowledgeEntry]:
    """Loads and returns every knowledge entry from the store, sorted by
    file path.
    """
    return [
        KnowledgeEntry.from_file(path)
        for path in list_knowledge_files(workspace_path)
    ]


def _is_within_directory(directory: str, target: str) -> bool:
    """Reports whether *target* resolves to a path inside *directory*.

    Both paths are canonicalized with `os.path.realpath` (resolving symlinks
    and ``..`` segments) before comparison, and `os.path.commonpath` is used
    so that a sibling directory sharing a name prefix (e.g. ``.../knowledge``
    vs ``.../knowledge-backup``) is not mistaken for a containment match.
    """
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)
    try:
        return os.path.commonpath([directory, target]) == directory
    except ValueError:
        # commonpath raises if the paths are on different drives / mixes of
        # absolute and relative; treat that as "not contained".
        return False


def find_knowledge_file(
    entry_id: str, workspace_path: str | None = None
) -> str | None:
    """Finds a knowledge file by exact ID or unique ID prefix.

    Returns the path on an exact or unique-prefix match. Returns ``None`` if
    no file matches. If the prefix is ambiguous, prints an error to stderr
    and returns ``None`` (matching the reports/tasks finder behaviour).

    Security: ``entry_id`` is untrusted (it comes straight from ``--id``).
    IDs containing path separators, parent references (``..``), or absolute
    paths are rejected up front, and every resolved candidate is verified to
    stay within the knowledge directory (`os.path.realpath` +
    `os.path.commonpath`). This chokepoint protects ``get``, ``edit``, and
    ``delete`` alike against path-traversal (see security report 6378212b).
    """
    import sys

    knowledge_dir = get_knowledge_dir(workspace_path)

    # Fast, explicit up-front guard (defense in depth): a legitimate entry ID
    # is a bare token and never contains a path separator, a parent
    # reference, or a drive/root. Reject such IDs before touching the disk.
    if (
        os.sep in entry_id
        or (os.altsep and os.altsep in entry_id)
        or ".." in entry_id.split("/")
        or ".." in entry_id.split(os.sep)
        or os.path.isabs(entry_id)
    ):
        return None

    # Try an exact match first.
    candidate = os.path.join(
        knowledge_dir, f"{entry_id}{KNOWLEDGE_FILE_SUFFIX}"
    )
    # Even with the up-front guard, verify containment on the resolved path
    # so that no crafted ID can escape the knowledge directory.
    if _is_within_directory(knowledge_dir, candidate) and os.path.isfile(
        candidate
    ):
        return candidate

    # Fall back to prefix matching over all entry files.
    matches = [
        p
        for p in list_knowledge_files(workspace_path)
        if os.path.basename(p).startswith(entry_id)
    ]

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        ids = [
            os.path.basename(p).removesuffix(KNOWLEDGE_FILE_SUFFIX)
            for p in matches
        ]
        print(
            f"Error: ambiguous ID prefix '{entry_id}' matches: "
            f"{', '.join(ids)}",
            file=sys.stderr,
        )
        return None
    return None


# ---------------------------------------------------------------------------
# Query helpers (pure; operate on already-loaded entries)
# ---------------------------------------------------------------------------

def filter_by_tag_expression(
    entries: list[KnowledgeEntry], expr: TagExpr
) -> list[KnowledgeEntry]:
    """Returns the entries whose tags satisfy the parsed tag expression."""
    return [
        entry
        for entry in entries
        if tag_expression_matches(entry.tags, expr)
    ]


def filter_by_regex(
    entries: list[KnowledgeEntry], pattern: "re.Pattern"
) -> list[KnowledgeEntry]:
    """Returns the entries whose searchable text matches the regex pattern.

    The pattern is applied with `re.Pattern.search` (partial match) over each
    entry's `searchable_text`.
    """
    return [
        entry
        for entry in entries
        if pattern.search(entry.searchable_text())
    ]


def query_entries(
    entries: list[KnowledgeEntry],
    expr: "TagExpr | None",
    pattern: "re.Pattern | None",
) -> list[KnowledgeEntry]:
    """Applies the tag-expression and regex filters, ANDed together.

    Either filter may be ``None`` (or a `MatchAll` expression), in which case
    that filter is skipped. When both are ``None`` (or a no-op), every entry
    is returned.
    """
    result = entries
    if expr is not None:
        result = filter_by_tag_expression(result, expr)
    if pattern is not None:
        result = filter_by_regex(result, pattern)
    return result


def tag_census(
    entries: list[KnowledgeEntry],
) -> list[tuple[str, int]]:
    """Counts how many entries carry each tag, grouped case-insensitively.

    Tags are grouped on their lowercased form and counted at most once per
    entry (duplicate tags within an entry do not inflate the count). The
    result is sorted by count descending, then by tag name ascending, and
    displays the lowercased canonical form of each tag.
    """
    counts: dict[str, int] = {}
    for entry in entries:
        # De-duplicate within the entry so a repeated tag counts once.
        seen: set[str] = set()
        for raw in entry.tags:
            tag = raw.strip().lower()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            counts[tag] = counts.get(tag, 0) + 1

    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))
