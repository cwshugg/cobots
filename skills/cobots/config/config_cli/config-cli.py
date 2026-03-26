#!/usr/bin/env python3
"""
config-cli.py - CLI for managing the cobots config file.

Provides commands to show the resolved config file path and to create a
default `cobots-config.yaml` if one does not already exist.
"""

import argparse
import os
import sys

# Resolve the `skills/cobots/` directory and add it to the module search path
# so skills can import shared packages (e.g. `config.base.constants`).
_SKILLS_COBOTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SKILLS_COBOTS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_COBOTS_DIR)

from config.base.config import CobotsConfig
from config.base.working_dir import resolve_config_path, resolve_working_dir


def main() -> int:
    """Parses arguments and manages the cobots config and working directory."""
    parser = argparse.ArgumentParser(
        description="CLI for managing the cobots config file and working directory."
    )
    parser.add_argument(
        "--show-path",
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
        help="Create a default config file if one does not already exist.",
    )

    args = parser.parse_args()

    if not args.show_path and not args.show_working_dir_path and not args.init:
        parser.print_help()
        return 1

    if args.show_path:
        print(resolve_config_path())
        return 0

    if args.show_working_dir_path:
        print(resolve_working_dir())
        return 0

    if args.init:
        working_dir = resolve_working_dir()
        config_path = resolve_config_path()
        if os.path.isfile(config_path):
            print(f"Already exists: {config_path}")
        else:
            os.makedirs(working_dir, exist_ok=True)
            CobotsConfig().write_file(config_path)
            print(f"Created: {config_path}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
