#!/usr/bin/env python3
"""
working-dir-cli.py - CLI for managing the cobots working directory.

Provides commands to show and create the `.cobots/` working directory where
agents store intermediate output and other working files.
"""

import argparse
import os
import sys

# Resolve the `skills/cobots/` directory and add it to the module search path
# so skills can import shared packages (e.g. `config.base.constants`).
_SKILLS_COBOTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SKILLS_COBOTS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_COBOTS_DIR)

from config.base.working_dir import resolve_working_dir


def main() -> int:
    """Parses arguments and manages the cobots working directory."""
    parser = argparse.ArgumentParser(
        description="CLI for managing the cobots working directory."
    )
    parser.add_argument(
        "--show-path",
        action="store_true",
        help="Print the resolved working directory path without modifying anything.",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create the working directory if it does not already exist.",
    )

    args = parser.parse_args()

    if not args.show_path and not args.init:
        parser.print_help()
        return 1

    working_dir = resolve_working_dir()

    if args.show_path:
        print(working_dir)
        return 0

    if args.init:
        if os.path.isdir(working_dir):
            print(f"Already exists: {working_dir}")
        else:
            os.makedirs(working_dir, exist_ok=True)
            print(f"Created: {working_dir}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
