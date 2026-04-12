#!/usr/bin/env python3
"""
tasks-cli.py - CLI for managing cobots tasks.

Provides subcommands to create, list, inspect, and update task files stored
under the `.cobots/tasks/` working directory.
"""

import argparse
import glob
import os
import re
import secrets
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

from cobots_lib.workspace.constants import TASK_FILE_SUFFIX, TASKS_DIR_NAME
from cobots_lib.workspace.working_dir import load_config, resolve_working_dir

# Path to the task template, in the same directory as this script.
TASK_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.task.md")

# Placeholder strings inside the task template.
PH_TASK_ID = "REPLACE_WITH_TASK_ID"
PH_TASK_TITLE = "REPLACE_WITH_TASK_TITLE"
PH_TASK_STATUS = "REPLACE_WITH_TASK_STATUS_STRING"
PH_TASK_AUTHOR = "REPLACE_WITH_NAME_OF_HUMAN_OR_AGENT_THAT_CREATED_THE_ITEM"
PH_TASK_OWNER = "REPLACE_WITH_NAME_OF_HUMAN_OR_AGENT_THAT_IS_WORKING_ON_THIS_ITEM"
PH_TASK_CREATED_TIMESTAMP = "REPLACE_WITH_CREATED_TIMESTAMP"
PH_LINKED_TASKS = "REPLACE_WITH_ARRAY_OF_LINKED_TASK_IDS"
PH_TASK_DESCRIPTION = "REPLACE_WITH_TASK_DESCRIPTION"

# Datetime format used in the created_timestamp frontmatter field.
TASK_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# Datetime format used in discussion headers.
DISCUSSION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Regex pattern matching a discussion header line.
DISCUSSION_HEADER_RE = re.compile(r"^## \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - .+$")

# Set by `main()` when `--workspace-path` is provided.
_WORKSPACE_PATH: str | None = None


# ---------------------------------------------------------------------------
# Task file helpers
# ---------------------------------------------------------------------------

def get_tasks_dir() -> str:
    """Returns the absolute path to the tasks directory."""
    return os.path.join(resolve_working_dir(_WORKSPACE_PATH), TASKS_DIR_NAME)


def list_task_files() -> list[str]:
    """Returns sorted absolute paths to all task files in the tasks directory."""
    tasks_dir = get_tasks_dir()
    pattern = os.path.join(tasks_dir, f"*{TASK_FILE_SUFFIX}")
    return sorted(glob.glob(pattern))


def find_task_file(task_id: str) -> str | None:
    """Finds a task file by exact or partial ID prefix.

    If `task_id` matches exactly one file (by full ID or unique prefix),
    returns its path. Returns ``None`` if no match is found. Prints an
    error and returns ``None`` if the prefix is ambiguous.
    """
    # Try exact match first.
    candidate = os.path.join(get_tasks_dir(), f"{task_id}{TASK_FILE_SUFFIX}")
    if os.path.isfile(candidate):
        return candidate

    # Fall back to prefix matching.
    matches = [
        p for p in list_task_files()
        if os.path.basename(p).startswith(task_id)
    ]

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        ids = [os.path.basename(p).removesuffix(TASK_FILE_SUFFIX) for p in matches]
        print(
            f"Error: ambiguous ID prefix '{task_id}' matches: {', '.join(ids)}",
            file=sys.stderr,
        )
        return None
    return None


def resolve_task(task_id: str) -> str | None:
    """Finds a task file by ID (exact or prefix), printing an error if not found.

    Returns the path on success, or ``None`` on failure (with an error
    already printed to stderr).
    """
    path = find_task_file(task_id)
    if path is None:
        print(f"Error: task '{task_id}' not found.", file=sys.stderr)
    return path


def get_linked_tasks(frontmatter: dict) -> list[str]:
    """Extracts the linked task list from frontmatter, always returning a list."""
    linked = frontmatter.get("linked_tasks", [])
    if not isinstance(linked, list):
        return []
    return linked


def task_id_from_path(path: str) -> str:
    """Extracts the full task ID from a task file path."""
    return os.path.basename(path).removesuffix(TASK_FILE_SUFFIX)


def sanitize_author(author: str) -> str:
    """Sanitizes an author name: strip, lowercase, whitespace to underscores."""
    return re.sub(r"\s+", "_", author.strip().lower())


def parse_task_file(path: str) -> tuple[dict, str]:
    """Parses a task file into its YAML frontmatter dict and body string.

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


def write_frontmatter(path: str, frontmatter: dict, body: str) -> None:
    """Writes a task file with updated frontmatter and the original body."""
    import yaml

    fm_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("---\n")
        fh.write(fm_str)
        fh.write("---")
        fh.write(body)


def generate_task_id(length: int) -> str:
    """Generates a random hex string of the given character length."""
    byte_count = (length + 1) // 2
    return secrets.token_hex(byte_count)[:length]


def format_linked_tasks(task_ids: list[str]) -> str:
    """Formats a list of task IDs as a YAML inline array string."""
    if not task_ids:
        return "[]"
    items = ", ".join(task_ids)
    return f"[{items}]"


def render_template(
    template: str,
    task_id: str,
    title: str,
    status: str,
    author: str,
    owner: str,
    created_timestamp: str,
    linked_tasks: list[str],
    description: str,
) -> str:
    """Replaces all placeholders in the template with the given values."""
    result = template
    result = result.replace(PH_TASK_ID, task_id)
    result = result.replace(PH_TASK_TITLE, title)
    result = result.replace(PH_TASK_STATUS, status)
    result = result.replace(PH_TASK_AUTHOR, author)
    result = result.replace(PH_TASK_OWNER, owner)
    result = result.replace(PH_TASK_CREATED_TIMESTAMP, created_timestamp)
    result = result.replace(PH_LINKED_TASKS, format_linked_tasks(linked_tasks))
    result = result.replace(PH_TASK_DESCRIPTION, description)
    return result


def get_latest_discussion(body: str) -> str | None:
    """Extracts the latest discussion entry from the task body.

    Returns the text from the last ``## Author - datetime`` header to the
    end of the body, or ``None`` if no discussion entries exist.
    """
    lines = body.splitlines()
    last_idx = None
    for i, line in enumerate(lines):
        if DISCUSSION_HEADER_RE.match(line.strip()):
            last_idx = i

    if last_idx is None:
        return None

    return "\n".join(lines[last_idx:]).rstrip()


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace, config) -> int:
    """Handles the ``create`` subcommand."""
    # Prompt the user and read the task description from STDIN.
    print("Enter the task description (press Ctrl+D when finished):", file=sys.stderr)
    description = sys.stdin.read().strip()
    if not description:
        print("Error: task description must be provided via STDIN.", file=sys.stderr)
        return 1

    # Load the template.
    template_path = os.path.normpath(TASK_TEMPLATE_PATH)
    if not os.path.isfile(template_path):
        print(f"Error: task template not found at {template_path}", file=sys.stderr)
        return 1

    with open(template_path, "r", encoding="utf-8") as fh:
        template = fh.read()

    # Parse linked task IDs from the comma-separated argument.
    linked_tasks = []
    if args.linked_tasks:
        linked_tasks = [t.strip() for t in args.linked_tasks.split(",") if t.strip()]

    # Capture the current UTC time for the frontmatter.
    now_utc = datetime.now(timezone.utc)
    created_timestamp = now_utc.strftime(TASK_TIMESTAMP_FORMAT)

    # Generate a task ID and render the template.
    task_id = generate_task_id(config.task_id_length)
    content = render_template(
        template=template,
        task_id=task_id,
        title=args.title,
        status=args.status,
        author=sanitize_author(args.author),
        owner=args.owner or "",
        created_timestamp=created_timestamp,
        linked_tasks=linked_tasks,
        description=description,
    )

    # Ensure the tasks directory exists and write the file.
    tasks_dir = get_tasks_dir()
    os.makedirs(tasks_dir, exist_ok=True)

    task_file = os.path.join(tasks_dir, f"{task_id}{TASK_FILE_SUFFIX}")
    with open(task_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(task_file)
    return 0


def cmd_list(args: argparse.Namespace, config) -> int:
    """Handles the ``list`` subcommand."""
    task_files = list_task_files()
    if not task_files:
        print("No tasks found.")
        return 0

    # Collect task metadata for filtering and display.
    tasks = []
    for path in task_files:
        fm, _ = parse_task_file(path)
        tasks.append((path, fm))

    # Apply filters.
    if args.owner:
        tasks = [(p, fm) for p, fm in tasks if fm.get("owner") == args.owner]
    if args.status:
        tasks = [(p, fm) for p, fm in tasks if fm.get("status") == args.status]

    if not tasks:
        print("No tasks match the given filters.")
        return 0

    # Sort by created_timestamp (ascending).
    tasks.sort(key=lambda t: t[1].get("created_timestamp", ""))

    for path, fm in tasks:
        task_id = fm.get("id", "???")
        created_ts = fm.get("created_timestamp", "???")
        title = fm.get("title", "(untitled)")
        status = fm.get("status", "(none)")
        owner = fm.get("owner", "")
        linked = get_linked_tasks(fm)

        # Build the display fragments.
        owner_str = f" owner={owner}" if owner else ""
        linked_str = f" linked=[{', '.join(str(t) for t in linked)}]" if linked else ""
        path_str = f" {path}" if args.show_path else ""

        print(f"[{task_id}] [{created_ts}] {title} ({status}){owner_str}{linked_str}{path_str}")

    return 0


def cmd_add_discussion(args: argparse.Namespace, config) -> int:
    """Handles the ``add-discussion`` subcommand."""
    task_path = resolve_task(args.id)
    if task_path is None:
        return 1

    # Read discussion content from STDIN.
    print("Enter discussion content (press Ctrl+D when finished):", file=sys.stderr)
    content = sys.stdin.read().strip()
    if not content:
        print("Error: discussion content must be provided via STDIN.", file=sys.stderr)
        return 1

    # Build the discussion header.
    now_utc = datetime.now(timezone.utc).strftime(DISCUSSION_DATETIME_FORMAT)
    header = f"## {now_utc} - {sanitize_author(args.author)}"

    # Read the existing file.
    with open(task_path, "r", encoding="utf-8") as fh:
        file_content = fh.read()

    # Strip trailing whitespace, then append a blank line + header + content.
    file_content = file_content.rstrip()
    file_content += f"\n\n{header}\n\n{content}\n"

    with open(task_path, "w", encoding="utf-8") as fh:
        fh.write(file_content)

    print(f"Discussion added to task {args.id}.")
    return 0


def cmd_set_status(args: argparse.Namespace, config) -> int:
    """Handles the ``set-status`` subcommand."""
    task_path = resolve_task(args.id)
    if task_path is None:
        return 1

    fm, body = parse_task_file(task_path)
    old_status = fm.get("status", "(none)")
    fm["status"] = args.status
    write_frontmatter(task_path, fm, body)

    print(f"Task {args.id}: {old_status} -> {args.status}")
    return 0


def cmd_get(args: argparse.Namespace, config) -> int:
    """Handles the ``get`` subcommand."""
    task_path = resolve_task(args.id)
    if task_path is None:
        return 1

    fm, body = parse_task_file(task_path)

    # Extract the description (text between the title heading and Discussion heading).
    description = ""
    body_lines = body.splitlines()
    desc_start = None
    desc_end = None
    for i, line in enumerate(body_lines):
        stripped = line.strip()
        # Skip until after the first `# Title` heading.
        if desc_start is None and stripped.startswith("# ") and not stripped.startswith("## "):
            desc_start = i + 1
            continue
        # Stop at the `# Discussion` heading.
        if desc_start is not None and stripped == "# Discussion":
            desc_end = i
            break

    if desc_start is not None:
        end = desc_end if desc_end is not None else len(body_lines)
        description = "\n".join(body_lines[desc_start:end]).strip()

    # Get latest discussion entry.
    latest_discussion = get_latest_discussion(body)

    # Print formatted output.
    print(f"Path:           {task_path}")
    print(f"ID:             {fm.get('id', '???')}")
    print(f"Created:        {fm.get('created_timestamp', '???')}")
    print(f"Title:          {fm.get('title', '(untitled)')}")
    print(f"Status:         {fm.get('status', '(none)')}")
    print(f"Author:         {fm.get('author', '(none)')}")
    print(f"Owner:          {fm.get('owner', '(none)')}")

    linked = get_linked_tasks(fm)
    print()
    print("Linked Tasks:")
    if linked:
        for link_id in linked:
            link_path = find_task_file(link_id)
            if link_path is not None:
                link_fm, _ = parse_task_file(link_path)
                link_title = link_fm.get("title", "(untitled)")
                link_status = link_fm.get("status", "(none)")
                link_owner = link_fm.get("owner", "")
                owner_str = f" (owner={link_owner})" if link_owner else ""
                print(f"  [{link_id}] {link_title} ({link_status}){owner_str}")
            else:
                print(f"  [{link_id}] (not found)")
    else:
        print("  (none)")

    print()
    print(f"Description:")
    print(f"  {description}" if description else "  (none)")

    print()
    if latest_discussion:
        print("Latest Discussion:")
        for line in latest_discussion.splitlines():
            print(f"  {line}")
    else:
        print("Latest Discussion: (none)")

    return 0


def cmd_add_link(args: argparse.Namespace, config) -> int:
    """Handles the ``add-link`` subcommand."""
    task_path = resolve_task(args.id)
    if task_path is None:
        return 1

    link_path = resolve_task(args.link_id)
    if link_path is None:
        return 1

    full_link_id = task_id_from_path(link_path)
    fm, body = parse_task_file(task_path)
    linked = get_linked_tasks(fm)

    if full_link_id in linked:
        print(f"Task {task_id_from_path(task_path)} is already linked to {full_link_id}.")
        return 0

    linked.append(full_link_id)
    fm["linked_tasks"] = linked
    write_frontmatter(task_path, fm, body)

    print(f"Linked {task_id_from_path(task_path)} -> {full_link_id}")
    return 0


def cmd_remove_link(args: argparse.Namespace, config) -> int:
    """Handles the ``remove-link`` subcommand."""
    task_path = resolve_task(args.id)
    if task_path is None:
        return 1

    # Resolve the link ID to a full ID for matching against stored values.
    link_path = resolve_task(args.link_id)
    if link_path is None:
        return 1

    full_link_id = task_id_from_path(link_path)
    fm, body = parse_task_file(task_path)
    linked = get_linked_tasks(fm)

    if full_link_id not in linked:
        print(f"Task {task_id_from_path(task_path)} is not linked to {full_link_id}.", file=sys.stderr)
        return 1

    linked.remove(full_link_id)
    fm["linked_tasks"] = linked
    write_frontmatter(task_path, fm, body)

    print(f"Unlinked {task_id_from_path(task_path)} -x- {full_link_id}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point. Parses subcommands and dispatches to handlers."""
    global _WORKSPACE_PATH

    parser = argparse.ArgumentParser(
        description="CLI for managing cobots tasks."
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
        help="Create a new task from the template.",
    )
    create_parser.add_argument("--title", required=True, help="The title of the task.")
    create_parser.add_argument("--author", required=True, help="The creator of the task.")
    create_parser.add_argument(
        "--status", required=True,
        help="The initial status of the task.",
    )
    create_parser.add_argument("--owner", default="", help="The owner working on the task.")
    create_parser.add_argument(
        "--linked-tasks", default="",
        help="Comma-separated list of linked task IDs.",
    )

    # -- list --
    list_parser = subparsers.add_parser(
        "list",
        help="List all tasks.",
    )
    list_parser.add_argument("--owner", default=None, help="Filter tasks by owner.")
    list_parser.add_argument(
        "--status", default=None,
        help="Filter tasks by status.",
    )
    list_parser.add_argument(
        "--show-path", action="store_true",
        help="Show the full file path for each task.",
    )

    # -- add-discussion --
    discuss_parser = subparsers.add_parser(
        "add-discussion",
        help="Add a discussion entry to a task.",
    )
    discuss_parser.add_argument("--id", required=True, help="The task ID.")
    discuss_parser.add_argument("--author", required=True, help="The author of the discussion.")

    # -- set-status --
    status_parser = subparsers.add_parser(
        "set-status",
        help="Update the status of a task.",
    )
    status_parser.add_argument("--id", required=True, help="The task ID.")
    status_parser.add_argument(
        "--status", required=True,
        help="The new status.",
    )

    # -- get --
    get_parser = subparsers.add_parser(
        "get",
        help="Show details of a task.",
    )
    get_parser.add_argument("--id", required=True, help="The task ID.")

    # -- add-link --
    add_link_parser = subparsers.add_parser(
        "add-link",
        help="Add a link from one task to another.",
    )
    add_link_parser.add_argument("--id", required=True, help="The task to add the link to.")
    add_link_parser.add_argument("--link-id", required=True, help="The task ID to link to.")

    # -- remove-link --
    remove_link_parser = subparsers.add_parser(
        "remove-link",
        help="Remove a link from one task to another.",
    )
    remove_link_parser.add_argument("--id", required=True, help="The task to remove the link from.")
    remove_link_parser.add_argument("--link-id", required=True, help="The task ID to unlink.")

    args = parser.parse_args()

    # Set the workspace path before any helpers are called.
    _WORKSPACE_PATH = args.workspace_path
    config = load_config(_WORKSPACE_PATH)

    # Validate status values against the loaded config where applicable.
    if hasattr(args, "status") and args.status is not None:
        if args.status not in config.task_status_values:
            valid = ", ".join(config.task_status_values)
            print(
                f"Error: invalid status '{args.status}' (choose from: {valid})",
                file=sys.stderr,
            )
            return 1

    handlers = {
        "create": cmd_create,
        "list": cmd_list,
        "add-discussion": cmd_add_discussion,
        "set-status": cmd_set_status,
        "get": cmd_get,
        "add-link": cmd_add_link,
        "remove-link": cmd_remove_link,
    }

    return handlers[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
