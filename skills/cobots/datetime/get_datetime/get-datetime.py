#!/usr/bin/env python3
"""
get-datetime.py - Command-line utility for retrieving the current datetime.

Provides formatted datetime output in UTC. Intended to be used as a skill
by agents that need to know the current date and time.
"""

import argparse
import sys
from datetime import datetime, timezone


# Output format: YYYY-MM-DD_HH-MM-SS (24-hour, UTC)
DATETIME_FORMAT = "%Y-%m-%d_%H-%M-%S"


def get_now() -> str:
    """Returns the current UTC datetime as a formatted string."""
    return datetime.now(timezone.utc).strftime(DATETIME_FORMAT)


def main() -> int:
    """Parses arguments and prints the requested datetime."""
    parser = argparse.ArgumentParser(
        description="Command-line utility for getting the current datetime in UTC."
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Print the current UTC datetime in YYYY-MM-DD_HH-MM-SS format.",
    )

    args = parser.parse_args()

    if args.now:
        print(get_now())
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
