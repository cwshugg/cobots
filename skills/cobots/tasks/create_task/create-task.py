#!/usr/bin/env python3
"""
create-task.py - Creates a new task from the task template.

Copies `tasks/task_template.md`, fills in the frontmatter with the provided
arguments, reads the task description from STDIN, generates a random hex ID
of the configured length, and saves the result under the working directory's
`tasks/` subdirectory.
"""

import argparse
import os
import secrets
import sys

# Resolve the `skills/cobots/` directory and add it to the module search path
# so skills can import shared packages (e.g. `config.base.constants`).
_SKILLS_COBOTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SKILLS_COBOTS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_COBOTS_DIR)

from config.base.constants import TASKS_DIR_NAME
from config.base.working_dir import load_config, resolve_working_dir

# Path to the task template, relative to this skill's parent directory.
TASK_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "template.task.md")

# Placeholder strings inside the task template.
PH_TASK_ID = "REPLACE_WITH_TASK_ID"
PH_TASK_TITLE = "REPLACE_WITH_TASK_TITLE"
PH_TASK_STATUS = "REPLACE_WITH_TASK_STATUS_STRING"
PH_TASK_AUTHOR = "REPLACE_WITH_NAME_OF_HUMAN_OR_AGENT_THAT_CREATED_THE_ITEM"
PH_TASK_DESCRIPTION = "REPLACE_WITH_TASK_DESCRIPTION"


def generate_task_id(length: int) -> str:
    """Generates a random hex string of the given character length."""
    byte_count = (length + 1) // 2
    return secrets.token_hex(byte_count)[:length]


def render_template(
    template: str,
    task_id: str,
    title: str,
    status: str,
    author: str,
    description: str,
) -> str:
    """Replaces all placeholders in the template with the given values."""
    result = template
    result = result.replace(PH_TASK_ID, task_id)
    result = result.replace(PH_TASK_TITLE, title)
    result = result.replace(PH_TASK_STATUS, status)
    result = result.replace(PH_TASK_AUTHOR, author)
    result = result.replace(PH_TASK_DESCRIPTION, description)
    return result


def main() -> int:
    """Parses arguments and creates a new task file."""
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Creates a new task from the task template."
    )
    parser.add_argument(
        "--title",
        required=True,
        help="The title of the task.",
    )
    parser.add_argument(
        "--author",
        required=True,
        help="The name of the human or agent creating the task.",
    )
    parser.add_argument(
        "--status",
        required=True,
        choices=config.task_status_values,
        help="The initial status of the task.",
    )

    args = parser.parse_args()

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

    # Generate a task ID and render the template.
    task_id = generate_task_id(config.task_id_length)
    content = render_template(
        template=template,
        task_id=task_id,
        title=args.title,
        status=args.status,
        author=args.author,
        description=description,
    )

    # Ensure the tasks directory exists under the working directory.
    tasks_dir = os.path.join(resolve_working_dir(), TASKS_DIR_NAME)
    os.makedirs(tasks_dir, exist_ok=True)

    # Write the task file.
    task_file = os.path.join(tasks_dir, f"{task_id}.task.md")
    with open(task_file, "w", encoding="utf-8") as fh:
        fh.write(content)

    print(task_file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
