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

# Activate the shared virtual environment so dependencies are available.
from venv.venv import activate_venv
activate_venv()

from cobots_lib.workspace.config import CobotsConfig
from cobots_lib.workspace.constants import REPORTS_DIR_NAME, TASKS_DIR_NAME
from cobots_lib.workspace.working_dir import resolve_config_path, resolve_working_dir


def main() -> int:
    """Parses arguments and manages the cobots workspace."""
    parser = argparse.ArgumentParser(
        description="CLI for managing the cobots workspace."
    )
    parser.add_argument(
        "--workspace-path",
        default=None,
        help="Explicit path to the .cobots/ workspace directory.",
    )
    parser.add_argument(
        "--show-config-path",
        action="store_true",
        help="Print the resolved config file path without modifying anything.",
    )
    parser.add_argument(
        "--show-workspace-path",
        action="store_true",
        help="Print the resolved working directory path without modifying anything.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize the full workspace (.cobots/, config, tasks/, reports/).",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Workspace name to set during --init (defaults to empty string).",
    )
    parser.add_argument(
        "--show-workspace-name",
        action="store_true",
        help="Print the current workspace name from the config and exit.",
    )

    args = parser.parse_args()

    if (
        not args.show_config_path
        and not args.show_workspace_path
        and not args.show_workspace_name
        and not args.init
    ):
        parser.print_help()
        return 1

    wp = args.workspace_path

    if args.show_config_path:
        print(resolve_config_path(wp))
        return 0

    if args.show_workspace_path:
        print(resolve_working_dir(wp))
        return 0

    if args.show_workspace_name:
        config_path = resolve_config_path(wp)
        if not os.path.isfile(config_path):
            print(
                "Error: workspace is not initialized "
                f"(config not found: {config_path})",
                file=sys.stderr,
            )
            return 1
        config = CobotsConfig.from_file(config_path)
        print(config.workspace_name)
        return 0

    if args.init:
        working_dir = resolve_working_dir(wp)
        config_path = resolve_config_path(wp)
        tasks_dir = os.path.join(working_dir, TASKS_DIR_NAME)
        reports_dir = os.path.join(working_dir, REPORTS_DIR_NAME)

        already_exists = os.path.isfile(config_path)

        # 1. Create the workspace directory.
        os.makedirs(working_dir, exist_ok=True)

        # 2. Create or update the config file.
        if not already_exists:
            CobotsConfig(workspace_name=args.name).write_file(config_path)
        elif args.name:
            # Update the workspace name if --name was explicitly provided
            # on a re-init of an existing workspace.
            config = CobotsConfig.from_file(config_path)
            config.workspace_name = args.name
            config.write_file(config_path)

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
