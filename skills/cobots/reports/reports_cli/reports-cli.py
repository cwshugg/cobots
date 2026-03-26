#!/usr/bin/env python3
"""
reports-cli.py - CLI for creating cobots reports.

Creates a new report from `template.report.md`, fills in the frontmatter
with the provided arguments, reads the report body from STDIN, and saves
the result under `.cobots/reports/`.
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone

# Resolve the `skills/cobots/` directory and add it to the module search path
# so skills can import shared packages (e.g. `workspace.base.constants`).
_SKILLS_COBOTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SKILLS_COBOTS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_COBOTS_DIR)

from workspace.base.constants import REPORTS_DIR_NAME, REPORT_FILE_SUFFIX
from workspace.base.working_dir import resolve_working_dir

# Path to the report template, relative to this skill's parent directory.
REPORT_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "template.report.md")

# Placeholder strings inside the report template.
PH_REPORT_TITLE = "REPLACE_WITH_REPORT_TITLE"
PH_REPORT_AUTHOR = "REPLACE_WITH_REPORT_AUTHOR"
PH_REPORT_CONTENTS = "REPLACE_WITH_REPORT_CONTENTS"

# Datetime format used in report file names.
REPORT_DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def slugify_title(title: str) -> str:
    """Converts a title to a lowercase, underscore-separated slug."""
    slug = title.strip().lower()
    slug = re.sub(r"\s+", "_", slug)
    slug = re.sub(r"[^\w_]", "", slug)
    return slug


def render_template(template: str, title: str, author: str, contents: str) -> str:
    """Replaces all placeholders in the template with the given values."""
    result = template
    result = result.replace(PH_REPORT_TITLE, title)
    result = result.replace(PH_REPORT_AUTHOR, author)
    result = result.replace(PH_REPORT_CONTENTS, contents)
    return result


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

    # Render the template.
    content = render_template(
        template=template,
        title=args.title,
        author=args.author,
        contents=contents,
    )

    # Build the file name.
    now_utc = datetime.now(timezone.utc).strftime(REPORT_DATETIME_FORMAT)
    slug = slugify_title(args.title)
    filename = f"{now_utc}_{slug}{REPORT_FILE_SUFFIX}"

    # Ensure the reports directory exists and write the file.
    reports_dir = os.path.join(resolve_working_dir(), REPORTS_DIR_NAME)
    os.makedirs(reports_dir, exist_ok=True)

    report_path = os.path.join(reports_dir, filename)
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(report_path)
    return 0


def main() -> int:
    """Entry point. Parses subcommands and dispatches to handlers."""
    parser = argparse.ArgumentParser(
        description="CLI for managing cobots reports."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- create --
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new report from the template.",
    )
    create_parser.add_argument("--title", required=True, help="The title of the report.")
    create_parser.add_argument("--author", required=True, help="The author of the report.")

    args = parser.parse_args()

    handlers = {
        "create": cmd_create,
    }

    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
