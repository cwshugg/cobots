#!/usr/bin/env python3
"""
workspace-cli.py - CLI for managing the cobots workspace.

Provides commands to initialize the workspace, and to show resolved paths
for the workspace directory and config file.
"""

import argparse
import os
import sys

# Resolve the `skills/` directory and add it to the module search path
# so skills can import shared packages (e.g. `cobots_lib.workspace.constants`).
_SKILLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.workspace.config import CobotsConfig
from cobots_lib.workspace.constants import REPORTS_DIR_NAME, TASKS_DIR_NAME
from cobots_lib.workspace.working_dir import resolve_config_path, resolve_working_dir


def main() -> int:
    """Parses arguments and manages the cobots workspace."""
    parser = argparse.ArgumentParser(
        description="CLI for managing the cobots workspace."
    )
    parser.add_argument(
        "--show-config-path",
        action="store_true",
        help="Print the resolved config file path without modifying anything.",
    )
    parser.add_argument(
        "--show-working-dir-path",
        action="store_true",
        help="Print the resolved working directory path without modifying anything.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the full workspace (.cobots/, config, tasks/, reports/).",
    )

    args = parser.parse_args()

    if not args.show_config_path and not args.show_working_dir_path and not args.init:
        parser.print_help()
        return 1

    if args.show_config_path:
        print(resolve_config_path())
        return 0

    if args.show_working_dir_path:
        print(resolve_working_dir())
        return 0

    if args.init:
        working_dir = resolve_working_dir()
        config_path = resolve_config_path()
        tasks_dir = os.path.join(working_dir, TASKS_DIR_NAME)
        reports_dir = os.path.join(working_dir, REPORTS_DIR_NAME)

        already_exists = os.path.isfile(config_path)

        # 1. Create the workspace directory.
        os.makedirs(working_dir, exist_ok=True)

        # 2. Create the config file.
        if not already_exists:
            CobotsConfig().write_file(config_path)

        # 3. Create the tasks directory.
        os.makedirs(tasks_dir, exist_ok=True)

        # 4. Create the reports directory.
        os.makedirs(reports_dir, exist_ok=True)

        if already_exists:
            print(f"Already initialized: {working_dir}")
        else:
            print(f"Initialized workspace: {working_dir}")

        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
