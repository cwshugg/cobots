"""
tui_mode.py - Launches the interactive Textual TUI.

This module is only imported when TUI mode is selected, ensuring
``textual`` is not loaded for the overview mode.
"""

import sys


def run_tui(args, status_config=None, cobots_config=None) -> None:
    """Launches the :class:`CobotsStatusApp` Textual application.

    Falls back to rich mode if stdout is not a TTY.  Prints a friendly
    message and exits with code 1 if ``textual`` is not installed.
    """
    if not sys.stdout.isatty():
        print(
            "Warning: TUI mode requires a TTY. Falling back to rich mode.",
            file=sys.stderr,
        )
        from modes.rich_mode import run_rich
        return run_rich(args, status_config=status_config, cobots_config=cobots_config)

    try:
        from tui.app import CobotsStatusApp
    except ImportError:
        print(
            "Error: The 'textual' package is required for TUI mode.\n"
            "Install it with:  pip install 'textual>=1.0,<2.0'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Resolve config if not already provided.
    if status_config is None:
        from config import load_status_config
        status_config, cobots_config = load_status_config(
            getattr(args, "workspace_path", None)
        )

    refresh_rate = args.refresh_rate
    no_refresh = getattr(args, "no_refresh", False)
    activity_count = args.activity_count
    workspace_path = getattr(args, "workspace_path", None)

    app = CobotsStatusApp(
        workspace_path=workspace_path,
        refresh_rate=refresh_rate,
        no_refresh=no_refresh,
        activity_count=activity_count,
        cobots_config=cobots_config,
    )
    app.run()
