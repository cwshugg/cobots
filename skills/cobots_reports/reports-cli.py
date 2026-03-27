#!/usr/bin/env python3
"""
reports-cli.py - CLI for creating and listing cobots reports.

Provides subcommands to create reports from `template.report.md` and to
list existing reports stored under `.cobots/reports/`.
"""

import argparse
import glob
import os
import re
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
from cobots_lib.workspace.working_dir import resolve_working_dir

# Path to the report template, in the same directory as this script.
REPORT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.report.md")

# Placeholder strings inside the report template.
PH_REPORT_TITLE = "REPLACE_WITH_REPORT_TITLE"
PH_REPORT_AUTHOR = "REPLACE_WITH_REPORT_AUTHOR"
PH_REPORT_TIMESTAMP = "REPLACE_WITH_CREATION_DATETIME"
PH_REPORT_CONTENTS = "REPLACE_WITH_REPORT_CONTENTS"

# Datetime format used in report file names.
REPORT_FILENAME_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"

# Datetime format used in the frontmatter timestamp field.
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


def parse_report_frontmatter(path: str) -> dict:
    """Parses a report file and returns its YAML frontmatter as a dict."""
    import yaml

    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    fm = yaml.safe_load(parts[1])
    return fm if fm is not None else {}


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
    title: str,
    author: str,
    timestamp: str,
    contents: str,
) -> str:
    """Replaces all placeholders in the template with the given values."""
    result = template
    result = result.replace(PH_REPORT_TITLE, title)
    result = result.replace(PH_REPORT_AUTHOR, author)
    result = result.replace(PH_REPORT_TIMESTAMP, timestamp)
    result = result.replace(PH_REPORT_CONTENTS, contents)
    return result


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> int:
    """Handles the ``create`` subcommand."""
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

    # Capture the current UTC time for both the file name and frontmatter.
    now_utc = datetime.now(timezone.utc)
    timestamp = now_utc.strftime(REPORT_TIMESTAMP_FORMAT)

    # Render the template.
    content = render_template(
        template=template,
        title=args.title,
        author=sanitize_author(args.author),
        timestamp=timestamp,
        contents=contents,
    )

    # Build the file name.
    filename_ts = now_utc.strftime(REPORT_FILENAME_DATETIME_FORMAT)
    slug = slugify_title(args.title)
    filename = f"{filename_ts}_{slug}{REPORT_FILE_SUFFIX}"

    # Ensure the reports directory exists and write the file.
    reports_dir = get_reports_dir()
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, filename)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(report_path)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handles the ``list`` subcommand."""
    report_files = list_report_files()
    if not report_files:
        print("No reports found.")
        return 0

    for path in report_files:
        fm = parse_report_frontmatter(path)
        timestamp = fm.get("timestamp", "???")
        author = fm.get("author", "(unknown)")
        title = fm.get("title", "(untitled)")
        path_str = f" {path}" if args.show_path else ""

        print(f"[{timestamp}] ({author}) {title}{path_str}")

    return 0


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

    # -- list --
    list_parser = subparsers.add_parser(
        "list",
        help="List all reports.",
    )
    list_parser.add_argument(
        "--show-path", action="store_true",
        help="Show the full file path for each report.",
    )

    args = parser.parse_args()

    _WORKSPACE_PATH = args.workspace_path

    handlers = {
        "create": cmd_create,
        "list": cmd_list,
    }

    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
