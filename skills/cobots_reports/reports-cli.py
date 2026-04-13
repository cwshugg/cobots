#!/usr/bin/env python3
"""
reports-cli.py - CLI for creating, listing, and inspecting cobots reports.

Provides subcommands to create reports from `template.report.md`, list
existing reports, and inspect individual reports stored under `.cobots/reports/`.
"""

import argparse
import glob
import os
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone

# Resolve the `skills/` directory and add it to the module search path
# so skills can import shared packages (e.g. `cobots_lib.workspace.constants`).
_SKILLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# Activate the shared virtual environment so dependencies are available.
from venv.venv import activate_venv
activate_venv()

from cobots_lib.workspace.constants import REPORTS_DIR_NAME, REPORT_FILE_SUFFIX
from cobots_lib.workspace.working_dir import load_config, resolve_working_dir

# Path to the report template, in the same directory as this script.
REPORT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.report.md")

# Placeholder strings inside the report template.
PH_REPORT_ID = "REPLACE_WITH_REPORT_ID"
PH_REPORT_TITLE = "REPLACE_WITH_REPORT_TITLE"
PH_REPORT_AUTHOR = "REPLACE_WITH_REPORT_AUTHOR"
PH_REPORT_TIMESTAMP = "REPLACE_WITH_CREATION_DATETIME"
PH_REPORT_CONTENTS = "REPLACE_WITH_REPORT_CONTENTS"

# Datetime format used in the created_timestamp frontmatter field.
REPORT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


# Set by `main()` when `--workspace-path` is provided.
_WORKSPACE_PATH: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_reports_dir() -> str:
    """Returns the absolute path to the reports directory."""
    return os.path.join(resolve_working_dir(_WORKSPACE_PATH), REPORTS_DIR_NAME)


def list_report_files() -> list[str]:
    """Returns sorted absolute paths to all report files in the reports directory."""
    pattern = os.path.join(get_reports_dir(), f"*{REPORT_FILE_SUFFIX}")
    return sorted(glob.glob(pattern))


def generate_report_id(length: int) -> str:
    """Generates a random hex string of the given character length."""
    byte_count = (length + 1) // 2
    return secrets.token_hex(byte_count)[:length]


def find_report_file(report_id: str) -> str | None:
    """Finds a report file by exact or partial ID prefix.

    If `report_id` matches exactly one file (by full ID or unique prefix),
    returns its path. Returns ``None`` if no match is found. Prints an
    error and returns ``None`` if the prefix is ambiguous.
    """
    # Try exact match first.
    candidate = os.path.join(get_reports_dir(), f"{report_id}{REPORT_FILE_SUFFIX}")
    if os.path.isfile(candidate):
        return candidate

    # Fall back to prefix matching.
    matches = [
        p for p in list_report_files()
        if os.path.basename(p).startswith(report_id)
    ]

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        ids = [os.path.basename(p).removesuffix(REPORT_FILE_SUFFIX) for p in matches]
        print(
            f"Error: ambiguous ID prefix '{report_id}' matches: {', '.join(ids)}",
            file=sys.stderr,
        )
        return None
    return None


def resolve_report(report_id: str) -> str | None:
    """Finds a report file by ID (exact or prefix), printing an error if not found.

    Returns the path on success, or ``None`` on failure (with an error
    already printed to stderr).
    """
    path = find_report_file(report_id)
    if path is None:
        print(f"Error: report '{report_id}' not found.", file=sys.stderr)
    return path


def report_id_from_path(path: str) -> str:
    """Extracts the full report ID from a report file path."""
    return os.path.basename(path).removesuffix(REPORT_FILE_SUFFIX)


def parse_report_file(path: str) -> tuple[dict, str]:
    """Parses a report file into its YAML frontmatter dict and body string.

    The frontmatter is the content between the first pair of ``---``
    delimiters. The body is everything after the closing delimiter.
    """
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    # Split on the `---` delimiters.
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1]
    body = parts[2]

    frontmatter = yaml.safe_load(frontmatter_str)
    if frontmatter is None:
        frontmatter = {}

    return frontmatter, body


def slugify_title(title: str) -> str:
    """Converts a title to a lowercase, underscore-separated slug."""
    slug = title.strip().lower()
    slug = re.sub(r"\s+", "_", slug)
    slug = re.sub(r"[^\w_]", "", slug)
    return slug


def sanitize_author(author: str) -> str:
    """Sanitizes an author name: strip, lowercase, whitespace to underscores."""
    return re.sub(r"\s+", "_", author.strip().lower())


def render_template(
    template: str,
    report_id: str,
    title: str,
    author: str,
    timestamp: str,
    contents: str,
) -> str:
    """Replaces all placeholders in the template with the given values."""
    result = template
    result = result.replace(PH_REPORT_ID, report_id)
    result = result.replace(PH_REPORT_TITLE, title)
    result = result.replace(PH_REPORT_AUTHOR, author)
    result = result.replace(PH_REPORT_TIMESTAMP, timestamp)
    result = result.replace(PH_REPORT_CONTENTS, contents)
    return result


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace, config) -> int:
    """Handles the ``create`` subcommand."""
    if args.empty:
        contents = ""
    else:
        print("Enter the report contents (press Ctrl+D when finished):", file=sys.stderr)
        contents = sys.stdin.read().strip()
        if not contents:
            print("Error: report contents must be provided via STDIN.", file=sys.stderr)
            return 1

    # Load the template.
    template_path = os.path.normpath(REPORT_TEMPLATE_PATH)
    if not os.path.isfile(template_path):
        print(f"Error: report template not found at {template_path}", file=sys.stderr)
        return 1

    with open(template_path, "r", encoding="utf-8") as fh:
        template = fh.read()

    # Capture the current UTC time for the frontmatter.
    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime(REPORT_TIMESTAMP_FORMAT)

    # Generate a report ID.
    report_id = generate_report_id(config.report_id_length)

    # Render the template.
    content = render_template(
        template=template,
        report_id=report_id,
        title=args.title,
        author=sanitize_author(args.author),
        timestamp=timestamp,
        contents=contents,
    )

    # Build the file name using the report ID.
    filename = f"{report_id}{REPORT_FILE_SUFFIX}"

    # Ensure the reports directory exists and write the file.
    reports_dir = get_reports_dir()
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, filename)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(report_path)
    return 0


def cmd_list(args: argparse.Namespace, config) -> int:
    """Handles the ``list`` subcommand."""
    report_files = list_report_files()
    if not report_files:
        print("No reports found.")
        return 0

    # Collect report metadata for sorting and display.
    reports = []
    for path in report_files:
        fm, _ = parse_report_file(path)
        reports.append((path, fm))

    # Sort by created_timestamp (ascending).
    reports.sort(key=lambda r: r[1].get("created_timestamp", ""))

    for path, fm in reports:
        report_id = fm.get("id", "???")
        created_ts = fm.get("created_timestamp", "???")
        author = fm.get("author", "(unknown)")
        title = fm.get("title", "(untitled)")
        path_str = f" {path}" if args.show_path else ""

        print(f"[{report_id}] [{created_ts}] ({author}) {title}{path_str}")

    return 0


def cmd_get(args: argparse.Namespace, config) -> int:
    """Handles the ``get`` subcommand."""
    report_path = resolve_report(args.id)
    if report_path is None:
        return 1

    fm, body = parse_report_file(report_path)

    # Extract the contents (text after the `# Title` heading).
    contents = ""
    body_lines = body.splitlines()
    content_start = None
    for i, line in enumerate(body_lines):
        stripped = line.strip()
        # Skip until after the first `# Title` heading.
        if content_start is None and stripped.startswith("# ") and not stripped.startswith("## "):
            content_start = i + 1
            continue

    if content_start is not None:
        contents = "\n".join(body_lines[content_start:]).strip()

    # Print formatted output.
    print(f"Path:           {report_path}")
    print(f"ID:             {fm.get('id', '???')}")
    print(f"Created:        {fm.get('created_timestamp', '???')}")
    print(f"Title:          {fm.get('title', '(untitled)')}")
    print(f"Author:         {fm.get('author', '(unknown)')}")

    print()
    print("Contents:")
    if contents:
        for line in contents.splitlines():
            print(f"  {line}")
    else:
        print("  (none)")

    return 0


def cmd_edit(args: argparse.Namespace, config) -> int:
    """Handles the ``edit`` subcommand.

    Opens the report file in the user's preferred editor (``$EDITOR``).
    """
    editor = os.environ.get("EDITOR")
    if not editor:
        print(
            "Error: EDITOR environment variable is not set. "
            "Please set it to your preferred editor "
            "(e.g., export EDITOR=vim).",
            file=sys.stderr,
        )
        return 1

    report_path = resolve_report(args.id)
    if report_path is None:
        return 1

    result = subprocess.run([editor, report_path])
    return 0 if result.returncode == 0 else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point. Parses subcommands and dispatches to handlers."""
    global _WORKSPACE_PATH

    parser = argparse.ArgumentParser(
        description="CLI for managing cobots reports."
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
        help="Create a new report from the template.",
    )
    create_parser.add_argument("--title", required=True, help="The title of the report.")
    create_parser.add_argument("--author", required=True, help="The author of the report.")
    create_parser.add_argument(
        "--empty", action="store_true",
        help="Create the report with empty contents, skipping STDIN.",
    )

    # -- list --
    list_parser = subparsers.add_parser(
        "list",
        help="List all reports.",
    )
    list_parser.add_argument(
        "--show-path", action="store_true",
        help="Show the full file path for each report.",
    )

    # -- get --
    get_parser = subparsers.add_parser(
        "get",
        help="Show details of a report.",
    )
    get_parser.add_argument("--id", required=True, help="The report ID.")

    # -- edit --
    edit_parser = subparsers.add_parser(
        "edit",
        help="Open a report file in the user's preferred editor.",
    )
    edit_parser.add_argument("--id", required=True, help="The report ID.")

    args = parser.parse_args()

    # Set the workspace path before any helpers are called.
    _WORKSPACE_PATH = args.workspace_path
    config = load_config(_WORKSPACE_PATH)

    handlers = {
        "create": cmd_create,
        "list": cmd_list,
        "get": cmd_get,
        "edit": cmd_edit,
    }

    return handlers[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
