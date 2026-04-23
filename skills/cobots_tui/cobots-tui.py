#!/usr/bin/env python3
"""
cobots-tui.py - CLI for viewing cobots workspace status.

Provides two modes: an interactive TUI (default) and a
``--show-overview`` flag that prints a rich-formatted snapshot and exits.
"""

import argparse
import sys
import os

# ---------------------------------------------------------------------------
# Bootstrap: add skills/ and this skill's own directory to sys.path.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)

# Activate the shared virtual environment so dependencies are available.
from venv.venv import activate_venv
activate_venv()

from config import load_status_config


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(
        description="View the current status of the cobots workspace.",
    )
    parser.add_argument(
        "--show-overview",
        action="store_true",
        default=False,
        dest="show_overview",
        help=(
            "Print a rich-formatted overview snapshot and exit "
            "(non-interactive)."
        ),
    )
    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=None,
        dest="refresh_rate",
        help="Auto-refresh interval in seconds (TUI only).",
    )
    parser.add_argument(
        "--activity-count",
        type=int,
        default=None,
        dest="activity_count",
        help="Number of activity events to display.",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        default=False,
        dest="no_refresh",
        help="Disable auto-refresh (TUI only).",
    )
    parser.add_argument(
        "--workspace-path",
        default=None,
        dest="workspace_path",
        help="Explicit path to the .cobots workspace directory.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse args, dispatch to TUI or overview mode."""
    args = parse_args()

    # Load config once and pass it through to avoid double-loading.
    status_config, cobots_config = load_status_config(
        getattr(args, "workspace_path", None)
    )

    # Apply config defaults for CLI args not explicitly provided.
    # When values are explicitly provided, clamp them to the same bounds
    # that StatusConfig enforces — prevents extreme values like
    # --refresh-rate 1 (disk I/O every second) or --activity-count 999999.
    if args.activity_count is None:
        args.activity_count = status_config.activity_count
    else:
        from cobots_lib.workspace.config import StatusConfig
        args.activity_count = max(
            StatusConfig.MIN_ACTIVITY_COUNT,
            min(args.activity_count, StatusConfig.MAX_ACTIVITY_COUNT),
        )
    if args.refresh_rate is None:
        args.refresh_rate = status_config.refresh_rate
    else:
        from cobots_lib.workspace.config import StatusConfig
        args.refresh_rate = max(
            StatusConfig.MIN_REFRESH_RATE,
            min(args.refresh_rate, StatusConfig.MAX_REFRESH_RATE),
        )

    if args.show_overview:
        from modes.rich_mode import run_rich
        return run_rich(
            args,
            status_config=status_config,
            cobots_config=cobots_config,
        )

    # Default: interactive TUI.
    from modes.tui_mode import run_tui
    return run_tui(
        args,
        status_config=status_config,
        cobots_config=cobots_config,
    )


if __name__ == "__main__":
    main()
