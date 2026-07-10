#!/usr/bin/env python3
"""
knowledge-cli.py - CLI for the cobots shared knowledge base.

Provides subcommands to create knowledge entries, list and query them by
boolean tag expression and/or a regex over title + content, inspect and edit
individual entries, delete entries, and print a per-tag census. Entries are
stored under `.cobots/knowledge/` as `{id}.knowledge.md` files with YAML
frontmatter, serialized via the shared `write_entry_file` writer.

The tag-expression grammar (used by both ``list --tags`` and ``query
--tags``) and single-tag validation are provided by the shared
`cobots_lib.workspace.tags` module; the entry model and query helpers live in
`cobots_lib.workspace.knowledge`. This CLI is a thin front-end over those.
"""

import argparse
import contextlib
import json
import os
import re
import secrets
import signal
import subprocess
import sys
from datetime import datetime, timezone

# Resolve the `skills/` directory and add it to the module search path
# so skills can import shared packages (e.g. `cobots_lib.workspace.tags`).
_SKILLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# Activate the shared virtual environment so dependencies are available.
from cobots_venv.venv import activate_venv
activate_venv()

from cobots_lib.workspace.constants import KNOWLEDGE_FILE_SUFFIX
from cobots_lib.workspace.knowledge import (
    KnowledgeEntry,
    find_knowledge_file,
    get_knowledge_dir,
    load_all_entries,
    query_entries,
    tag_census,
)
from cobots_lib.workspace.tags import (
    TagError,
    parse_tag_expression,
    validate_tags,
)
from cobots_lib.workspace.working_dir import load_config

# Datetime format used in the timestamp frontmatter fields.
KNOWLEDGE_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Wall-clock budget (seconds) for evaluating a user-supplied ``query
# --regex``. Python's stdlib ``re`` engine backtracks and has no built-in
# timeout, so a catastrophic pattern (e.g. ``(a+)+$``) can hang the process
# (ReDoS; security report 6378212b, finding 3). We bound the whole match
# phase with a SIGALRM-based deadline. Tradeoff: SIGALRM only exists on
# POSIX and only fires on the main thread, so on Windows this guard is a
# no-op and the ReDoS risk there is mitigated only by documentation — the
# CLI runs the match on the main thread, which is the common case.
REGEX_MATCH_TIMEOUT_SECONDS = 5


# Set by `main()` when `--workspace-path` is provided.
_WORKSPACE_PATH: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _wall_clock_timeout(seconds: int):
    """Best-effort wall-clock timeout using SIGALRM (POSIX main thread only).

    Yields to the wrapped block and raises `TimeoutError` if it runs longer
    than *seconds*. On platforms without `signal.SIGALRM` (e.g. Windows) or
    when not on the main thread, the guard degrades to a no-op — see the note
    on `REGEX_MATCH_TIMEOUT_SECONDS`.
    """
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum, frame):
        raise TimeoutError("operation timed out")

    try:
        previous = signal.signal(signal.SIGALRM, _handler)
    except ValueError:
        # Not on the main thread; cannot install the handler.
        yield
        return

    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _now_timestamp() -> str:
    """Returns the current UTC time formatted for frontmatter."""
    return datetime.now(timezone.utc).strftime(KNOWLEDGE_TIMESTAMP_FORMAT)


def generate_knowledge_id(length: int) -> str:
    """Generates a random hex string of the given character length."""
    byte_count = (length + 1) // 2
    return secrets.token_hex(byte_count)[:length]


def sanitize_author(author: str) -> str:
    """Sanitizes an author name: strip, lowercase, whitespace to underscores."""
    return re.sub(r"\s+", "_", author.strip().lower())


def read_entry_file(path: str) -> tuple[dict, str]:
    """Parses an entry file into its YAML frontmatter dict and body string.

    The frontmatter is the content between the first pair of ``---``
    delimiters; the body is everything after the closing delimiter.

    Raises:
        yaml.YAMLError: if the frontmatter block is not valid YAML. Callers
            (``cmd_edit``) catch this and surface a clean input error rather
            than a traceback, matching `parse_frontmatter`'s defensive read
            behaviour (security report 6378212b, finding 5).
    """
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = yaml.safe_load(parts[1])
    if frontmatter is None:
        frontmatter = {}
    return frontmatter, parts[2]


def write_entry_file(path: str, frontmatter: dict, body: str) -> None:
    """Writes an entry file from a frontmatter dict and a body string.

    The frontmatter key order is normalized so that rewritten files keep a
    stable, human-readable field ordering.
    """
    import yaml

    # Preserve a stable field ordering for readability across rewrites.
    ordered_keys = [
        "id",
        "title",
        "author",
        "created_timestamp",
        "updated_timestamp",
        "tags",
    ]
    ordered: dict = {}
    for key in ordered_keys:
        if key in frontmatter:
            ordered[key] = frontmatter[key]
    # Include any unexpected extra keys so hand-added fields are not lost.
    for key, value in frontmatter.items():
        if key not in ordered:
            ordered[key] = value

    fm_str = yaml.dump(
        ordered,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("---\n")
        fh.write(fm_str)
        fh.write("---")
        fh.write(body)


def entry_id_from_path(path: str) -> str:
    """Extracts the full entry ID from a knowledge file path."""
    return os.path.basename(path).removesuffix(KNOWLEDGE_FILE_SUFFIX)


def resolve_entry_path(entry_id: str) -> str | None:
    """Resolves an entry file by ID (exact or unique prefix).

    Returns the path on success, or ``None`` on failure. On an ambiguous
    prefix `find_knowledge_file` has already printed a message; on a plain
    not-found this function prints the error.
    """
    path = find_knowledge_file(entry_id, _WORKSPACE_PATH)
    if path is None:
        # Distinguish "ambiguous" (already reported by the finder) from
        # "not found" by re-checking whether any prefix matched at all.
        matches = [
            p
            for p in _all_entry_paths()
            if os.path.basename(p).startswith(entry_id)
        ]
        if not matches:
            print(
                f"Error: knowledge entry '{entry_id}' not found.",
                file=sys.stderr,
            )
    return path


def _all_entry_paths() -> list[str]:
    """Returns the sorted paths of all entry files (thin wrapper)."""
    from cobots_lib.workspace.knowledge import list_knowledge_files

    return list_knowledge_files(_WORKSPACE_PATH)


def format_entry_line(entry: KnowledgeEntry, show_path: bool) -> str:
    """Formats a single entry as one output line for list/query.

    Format: ``[{id}] [{created_timestamp}] ({author}) {title} #t1 #t2`` with
    an optional trailing path.
    """
    tags = " ".join(f"#{tag.strip().lower()}" for tag in entry.tags)
    tags_str = f" {tags}" if tags else ""
    path_str = f" {entry.path}" if show_path else ""
    created = entry.created_timestamp or "???"
    author = entry.author or "(unknown)"
    title = entry.title or "(untitled)"
    entry_id = entry.id or "???"
    return f"[{entry_id}] [{created}] ({author}) {title}{tags_str}{path_str}"


def _sorted_by_created(
    entries: list[KnowledgeEntry],
) -> list[KnowledgeEntry]:
    """Returns entries sorted by created_timestamp ascending."""
    return sorted(entries, key=lambda e: e.created_timestamp or "")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _body_starts_with_h1(contents: str) -> bool:
    """Reports whether *contents* begins with its own H1 (``# ``) heading.

    The first non-blank line is inspected; leading blank lines are ignored.
    """
    for line in contents.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith("# ")
    return False


def _compose_body(title: str, contents: str) -> str:
    """Composes an entry body, prepending an H1 title for readability.

    The KB keeps an H1 title at the top of each entry body so entries are
    readable standalone (design report 6d9b6d82, section 4.1). To avoid a
    duplicate heading, the ``# {title}`` line is only injected when *contents*
    does not already begin with its own H1. ``create`` and ``edit --body``
    share this helper so both behave consistently.
    """
    contents = contents.strip()
    if _body_starts_with_h1(contents):
        return f"\n\n{contents}\n"
    return f"\n\n# {title}\n\n{contents}\n"


def cmd_create(args: argparse.Namespace, config) -> int:
    """Handles the ``create`` subcommand."""
    # Validate tags first (invalid tags are a user-input error -> exit 2).
    raw_tags = args.tags.split()
    try:
        tags = validate_tags(raw_tags)
    except TagError as err:
        print(f"Error: invalid tags: {err}", file=sys.stderr)
        return 2

    # Read the body from STDIN unless an empty entry was requested.
    if args.empty:
        contents = ""
    else:
        print(
            "Enter the knowledge entry contents "
            "(press Ctrl+D when finished):",
            file=sys.stderr,
        )
        contents = sys.stdin.read().strip()
        if not contents:
            print(
                "Error: knowledge contents must be provided via STDIN.",
                file=sys.stderr,
            )
            return 1

    timestamp = _now_timestamp()
    entry_id = generate_knowledge_id(config.knowledge_id_length)

    # Build the frontmatter as a dict and serialize it via the shared,
    # YAML-safe writer instead of string-substituting untrusted values into a
    # hand-written template. This closes the frontmatter-injection vector
    # where a crafted --title could forge/corrupt frontmatter keys (security
    # report 6378212b, finding 2). create and edit now share one serializer.
    frontmatter = {
        "id": entry_id,
        "title": args.title,
        "author": sanitize_author(args.author),
        "created_timestamp": timestamp,
        "updated_timestamp": timestamp,
        "tags": tags,
    }
    # Compose the body with a leading H1 title for standalone readability
    # (unless the supplied contents already begin with their own H1).
    body = _compose_body(args.title, contents)

    knowledge_dir = get_knowledge_dir(_WORKSPACE_PATH)
    os.makedirs(knowledge_dir, exist_ok=True)

    entry_path = os.path.join(
        knowledge_dir, f"{entry_id}{KNOWLEDGE_FILE_SUFFIX}"
    )
    write_entry_file(entry_path, frontmatter, body)

    print(entry_path)
    return 0


def cmd_list(args: argparse.Namespace, config) -> int:
    """Handles the ``list`` subcommand."""
    entries = load_all_entries(_WORKSPACE_PATH)

    # Optional tag-expression filter, reusing the shared parser/evaluator.
    filtered = args.tags is not None
    if filtered:
        try:
            expr = parse_tag_expression(args.tags)
        except TagError as err:
            print(f"Error: invalid tag expression: {err}", file=sys.stderr)
            return 2
        entries = query_entries(entries, expr, None)

    if not entries:
        if filtered:
            print("No matching knowledge entries.")
        else:
            print("No knowledge entries found.")
        return 0

    for entry in _sorted_by_created(entries):
        print(format_entry_line(entry, args.show_path))
    return 0


def cmd_query(args: argparse.Namespace, config) -> int:
    """Handles the ``query`` subcommand."""
    entries = load_all_entries(_WORKSPACE_PATH)

    # Parse the optional tag expression (shared with ``list``).
    expr = None
    if args.tags is not None:
        try:
            expr = parse_tag_expression(args.tags)
        except TagError as err:
            print(f"Error: invalid tag expression: {err}", file=sys.stderr)
            return 2

    # Compile the optional regex over title + content.
    pattern = None
    if args.regex is not None:
        flags = re.IGNORECASE if args.ignore_case else 0
        try:
            pattern = re.compile(args.regex, flags)
        except re.error as err:
            print(f"Error: invalid regex: {err}", file=sys.stderr)
            return 2

    # AND both filters together (either may be a no-op). Bound the regex
    # match phase with a wall-clock deadline to mitigate ReDoS from a
    # catastrophic user-supplied pattern (security report 6378212b, finding 3).
    try:
        with _wall_clock_timeout(REGEX_MATCH_TIMEOUT_SECONDS):
            results = query_entries(entries, expr, pattern)
    except TimeoutError:
        print(
            "Error: regex evaluation timed out after "
            f"{REGEX_MATCH_TIMEOUT_SECONDS}s (pattern may be too complex).",
            file=sys.stderr,
        )
        return 2

    if not results:
        print("No matching knowledge entries.")
        return 0

    for entry in _sorted_by_created(results):
        print(format_entry_line(entry, args.show_path))
    return 0


def cmd_get(args: argparse.Namespace, config) -> int:
    """Handles the ``get`` subcommand."""
    path = resolve_entry_path(args.id)
    if path is None:
        return 1

    entry = KnowledgeEntry.from_file(path)
    tags_str = ", ".join(tag.strip().lower() for tag in entry.tags)

    print(f"Path:           {entry.path}")
    print(f"ID:             {entry.id or '???'}")
    print(f"Created:        {entry.created_timestamp or '???'}")
    print(f"Updated:        {entry.updated_timestamp or '???'}")
    print(f"Title:          {entry.title or '(untitled)'}")
    print(f"Author:         {entry.author or '(unknown)'}")
    print(f"Tags:           {tags_str or '(none)'}")

    print()
    print("Contents:")
    contents = entry.body.strip()
    if contents:
        for line in contents.splitlines():
            print(f"  {line}")
    else:
        print("  (none)")
    return 0


def _replace_h1_title(body: str, new_title: str) -> str:
    """Replaces the first H1 heading in *body* with *new_title*.

    The KB keeps an H1 title in the entry body for standalone readability, so
    ``edit --title`` must update it alongside the frontmatter. Only the first
    ``# `` heading is rewritten; if none exists the body is returned
    unchanged.
    """
    lines = body.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("# "):
            newline = "\n" if line.endswith("\n") else ""
            lines[i] = f"# {new_title}{newline}"
            break
    return "".join(lines)


def cmd_edit(args: argparse.Namespace, config) -> int:
    """Handles the ``edit`` subcommand (non-interactive or ``$EDITOR``)."""
    path = resolve_entry_path(args.id)
    if path is None:
        return 1

    has_update = any(
        [
            args.add_tags is not None,
            args.remove_tags is not None,
            args.set_tags is not None,
            args.title is not None,
            args.body,
        ]
    )

    # No update flags: fall back to opening the file in $EDITOR.
    if not has_update:
        editor = os.environ.get("EDITOR")
        if not editor:
            print(
                "Error: EDITOR environment variable is not set. "
                "Please set it to your preferred editor "
                "(e.g., export EDITOR=vim).",
                file=sys.stderr,
            )
            return 1
        result = subprocess.run([editor, path])
        return 0 if result.returncode == 0 else 1

    # --set-tags is mutually exclusive with --add-tags / --remove-tags.
    if args.set_tags is not None and (
        args.add_tags is not None or args.remove_tags is not None
    ):
        print(
            "Error: --set-tags cannot be combined with "
            "--add-tags/--remove-tags.",
            file=sys.stderr,
        )
        return 2

    # Read the entry, degrading gracefully on malformed frontmatter instead
    # of aborting with a traceback (security report 6378212b, finding 5).
    import yaml

    try:
        frontmatter, body = read_entry_file(path)
    except yaml.YAMLError as err:
        print(
            f"Error: could not parse frontmatter of {path}: {err}",
            file=sys.stderr,
        )
        return 2

    # Resolve the current tag list (lowercased) for mutation.
    current_tags = frontmatter.get("tags", [])
    if isinstance(current_tags, str):
        current_tags = [current_tags]
    elif not isinstance(current_tags, list):
        current_tags = []
    current_tags = [str(tag).strip().lower() for tag in current_tags]

    # Apply tag mutations.
    try:
        if args.set_tags is not None:
            current_tags = validate_tags(args.set_tags.split())
        else:
            if args.remove_tags is not None:
                to_remove = {
                    tag.strip().lower() for tag in args.remove_tags.split()
                }
                current_tags = [
                    tag for tag in current_tags if tag not in to_remove
                ]
            if args.add_tags is not None:
                added = validate_tags(args.add_tags.split())
                for tag in added:
                    if tag not in current_tags:
                        current_tags.append(tag)
    except TagError as err:
        print(f"Error: invalid tags: {err}", file=sys.stderr)
        return 2

    # Every edited entry must retain at least one tag.
    if not current_tags:
        print(
            "Error: an entry must retain at least one tag.",
            file=sys.stderr,
        )
        return 2

    frontmatter["tags"] = current_tags

    # Apply a title change (frontmatter + H1 in the body).
    if args.title is not None:
        frontmatter["title"] = args.title
        body = _replace_h1_title(body, args.title)

    # Replace the body from STDIN if requested. Reuse the shared composer so
    # the H1 title is only injected when the new body lacks one, keeping
    # ``edit --body`` consistent with ``create`` and avoiding a duplicate H1.
    if args.body:
        new_body = sys.stdin.read()
        title = frontmatter.get("title", "")
        body = _compose_body(title, new_body)

    # Any successful change refreshes the updated timestamp.
    frontmatter["updated_timestamp"] = _now_timestamp()

    write_entry_file(path, frontmatter, body)
    print(f"Updated: {path}")
    return 0


def cmd_delete(args: argparse.Namespace, config) -> int:
    """Handles the ``delete`` subcommand."""
    path = resolve_entry_path(args.id)
    if path is None:
        return 1

    if not (args.force or args.yes):
        print(
            f"Delete knowledge entry {entry_id_from_path(path)}? [y/N] ",
            end="",
            file=sys.stderr,
            flush=True,
        )
        answer = sys.stdin.readline().strip().lower()
        if answer not in ("y", "yes"):
            print("Deletion cancelled.", file=sys.stderr)
            return 1

    os.remove(path)
    print(f"Deleted: {path}")
    return 0


def cmd_tags(args: argparse.Namespace, config) -> int:
    """Handles the ``tags`` subcommand (per-tag census)."""
    entries = load_all_entries(_WORKSPACE_PATH)
    census = tag_census(entries)

    if args.sort == "name":
        census = sorted(census, key=lambda item: item[0])

    if args.json:
        print(
            json.dumps(
                [{"tag": tag, "count": count} for tag, count in census]
            )
        )
        return 0

    if not census:
        print("No tags found.")
        return 0

    # Align the count column to the longest tag name (min width for header).
    width = max([len(tag) for tag, _ in census] + [len("TAG")])
    print(f"{'TAG'.ljust(width)}  COUNT")
    for tag, count in census:
        print(f"{tag.ljust(width)}  {count}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Builds and returns the top-level argument parser."""
    parser = argparse.ArgumentParser(
        description="CLI for managing the cobots knowledge base."
    )
    parser.add_argument(
        "--workspace-path",
        default=None,
        help="Explicit path to the .cobots/ workspace directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- create --
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new knowledge entry.",
    )
    create_parser.add_argument(
        "--title", required=True, help="The title of the entry."
    )
    create_parser.add_argument(
        "--author", required=True, help="The author of the entry."
    )
    create_parser.add_argument(
        "--tags",
        required=True,
        help="Whitespace-separated tag names, e.g. 'git cli python'. "
        "This is a plain tag list, not a boolean expression.",
    )
    create_parser.add_argument(
        "--empty",
        action="store_true",
        help="Create the entry with empty contents, skipping STDIN.",
    )

    # -- list --
    list_parser = subparsers.add_parser(
        "list",
        help="List entries, optionally filtered by a tag expression.",
    )
    list_parser.add_argument(
        "--tags",
        default=None,
        help="A boolean tag expression to filter by, e.g. 'git and !rust'. "
        "Prefer single quotes in bash.",
    )
    list_parser.add_argument(
        "--show-path",
        action="store_true",
        help="Show the full file path for each entry.",
    )

    # -- query --
    query_parser = subparsers.add_parser(
        "query",
        help="Filter entries by a tag expression and/or a regex.",
    )
    query_parser.add_argument(
        "--tags",
        default=None,
        help="A boolean tag expression, e.g. 'git and (rust or c)'.",
    )
    query_parser.add_argument(
        "--regex",
        default=None,
        help="A regular expression matched against each entry's title "
        "and body.",
    )
    query_parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Apply case-insensitive matching to --regex.",
    )
    query_parser.add_argument(
        "--show-path",
        action="store_true",
        help="Show the full file path for each entry.",
    )

    # -- get --
    get_parser = subparsers.add_parser(
        "get",
        help="Show full details of an entry.",
    )
    get_parser.add_argument("--id", required=True, help="The entry ID.")

    # -- edit --
    edit_parser = subparsers.add_parser(
        "edit",
        help="Update an entry non-interactively, or open it in $EDITOR.",
    )
    edit_parser.add_argument("--id", required=True, help="The entry ID.")
    edit_parser.add_argument(
        "--add-tags",
        default=None,
        help="Whitespace-separated tags to add (plain list).",
    )
    edit_parser.add_argument(
        "--remove-tags",
        default=None,
        help="Whitespace-separated tags to remove (plain list).",
    )
    edit_parser.add_argument(
        "--set-tags",
        default=None,
        help="Whitespace-separated tags that replace the entire tag set. "
        "Mutually exclusive with --add-tags/--remove-tags.",
    )
    edit_parser.add_argument(
        "--title",
        default=None,
        help="A new title (updates the frontmatter and the body H1).",
    )
    edit_parser.add_argument(
        "--body",
        action="store_true",
        help="Read a new full body from STDIN, replacing the existing one.",
    )

    # -- delete --
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete an entry file by ID.",
    )
    delete_parser.add_argument("--id", required=True, help="The entry ID.")
    delete_parser.add_argument(
        "--force",
        "--yes",
        dest="force",
        action="store_true",
        help="Bypass the interactive confirmation prompt.",
    )
    # Keep a distinct `yes` attribute so both spellings are always defined.
    delete_parser.set_defaults(yes=False)

    # -- tags --
    tags_parser = subparsers.add_parser(
        "tags",
        help="List all tags with per-tag entry counts.",
    )
    tags_parser.add_argument(
        "--sort",
        choices=["count", "name"],
        default="count",
        help="Sort by count (default) or tag name.",
    )
    tags_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )

    return parser


def main() -> int:
    """Entry point. Parses subcommands and dispatches to handlers."""
    global _WORKSPACE_PATH

    parser = _build_parser()
    args = parser.parse_args()

    # Set the workspace path before any helpers are called.
    _WORKSPACE_PATH = args.workspace_path
    config = load_config(_WORKSPACE_PATH)

    handlers = {
        "create": cmd_create,
        "list": cmd_list,
        "query": cmd_query,
        "get": cmd_get,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "tags": cmd_tags,
    }

    return handlers[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
