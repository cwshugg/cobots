#!/usr/bin/env python3
"""
ntfy-cli.py - CLI for sending push notifications via ntfy.sh.

Provides subcommands to send notifications, send a test notification, and
display the current ntfy configuration from the cobots workspace.
"""

import argparse
import sys
import os

# Resolve the `skills/` directory and add it to the module search path
# so skills can import shared packages (e.g. `cobots_lib.workspace.constants`).
_SKILLS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# Activate the shared virtual environment so dependencies are available.
from venv.venv import activate_venv
activate_venv()

from cobots_lib.workspace.working_dir import load_config
from cobots_lib.ntfy.client import (
    NtfyClient,
    PRIORITY_NAMES,
    VALID_PRIORITIES,
)



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def resolve_priority(value: str) -> int:
    """Resolves a priority string to its integer value.

    Accepts either a numeric string ("1"–"5") or a name from
    `PRIORITY_NAMES` (e.g. "high", "urgent").

    Args:
        value: The priority string to resolve.

    Returns:
        The integer priority value.

    Raises:
        ValueError: If the value cannot be resolved to a valid priority.
    """
    # Try as an integer first.  The int() conversion is isolated in the
    # try/except so that a deliberate ValueError for out-of-range values
    # is not accidentally swallowed by the same handler.
    parsed_int: int | None = None
    try:
        parsed_int = int(value)
    except ValueError:
        pass

    if parsed_int is not None:
        if parsed_int in VALID_PRIORITIES:
            return parsed_int
        raise ValueError(
            f"invalid priority {parsed_int}: must be 1–5"
        )

    # Try as a named priority.
    name = value.strip().lower()
    if name in PRIORITY_NAMES:
        return PRIORITY_NAMES[name]

    valid_names = ", ".join(sorted(PRIORITY_NAMES.keys()))
    raise ValueError(
        f"invalid priority {value!r}: must be 1–5 or one of "
        f"{valid_names}"
    )


def mask_token(token: str) -> str:
    """Masks an ntfy token for display.

    Shows the first 5 characters followed by ``"... (set)"``, or returns
    ``"(not set)"`` if the token is empty.

    Args:
        token: The raw token string.

    Returns:
        The masked token string suitable for display.
    """
    if not token:
        return "(not set)"
    if len(token) < 6:
        return "(set)"
    return f"{token[:5]}... (set)"


def build_client(config, args: argparse.Namespace) -> NtfyClient:
    """Creates an `NtfyClient` using config values with CLI overrides.

    CLI arguments ``--url``, ``--topic``, and ``--token`` take precedence
    over the values stored in the workspace config.

    Args:
        config: A `CobotsConfig` instance.
        args: Parsed CLI arguments (may contain url, topic, token).

    Returns:
        An `NtfyClient` ready to send notifications.

    Raises:
        ValueError: If the resolved topic or URL is empty/invalid.
    """
    url = getattr(args, "url", None) or config.ntfy.url
    topic = getattr(args, "topic", None) or config.ntfy.topic
    token = getattr(args, "token", None) or config.ntfy.token

    return NtfyClient(url=url, topic=topic, token=token)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_send(args: argparse.Namespace, config) -> int:
    """Handles the ``send`` subcommand.

    Publishes a notification to the configured ntfy topic. The message
    body comes from ``--message`` or STDIN. Prints the resulting message
    ID on success or an error description on failure.
    """
    # Determine the message body.
    message = args.message
    if not message:
        if not sys.stdin.isatty():
            message = sys.stdin.read().strip()
        if not message:
            print("Error: message is required via --message or STDIN.",
                  file=sys.stderr)
            return 1

    # Resolve optional priority.
    priority = None
    if args.priority is not None:
        try:
            priority = resolve_priority(args.priority)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    # Parse comma-separated tags.
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    # Build the client with CLI overrides.
    try:
        client = build_client(config, args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Send the notification.
    try:
        result = client.send(
            message,
            title=args.title,
            priority=priority,
            tags=tags,
            click=args.click,
            markdown=args.markdown,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.success:
        print(f"Sent: {result.message_id}")
        return 0

    print(f"Error: {result.error}", file=sys.stderr)
    return 1


def cmd_test(args: argparse.Namespace, config) -> int:
    """Handles the ``test`` subcommand.

    Sends a predefined test notification to verify that the ntfy
    configuration is working correctly.
    """
    try:
        client = build_client(config, args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        result = client.send(
            "Cobots ntfy test notification",
            title="Cobots Test",
            tags=["white_check_mark"],
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.success:
        print(f"Sent: {result.message_id}")
        return 0

    print(f"Error: {result.error}", file=sys.stderr)
    return 1


def cmd_show_config(args: argparse.Namespace, config) -> int:
    """Handles the ``show-config`` subcommand.

    Prints the resolved ntfy settings from the workspace configuration,
    masking the token for security.
    """
    ntfy = config.ntfy
    print("ntfy configuration:")
    print(f"  url:   {ntfy.url}")
    print(f"  topic: {ntfy.topic or '(not set)'}")
    print(f"  token: {mask_token(ntfy.token)}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point. Parses subcommands and dispatches to handlers."""

    parser = argparse.ArgumentParser(
        description="CLI for sending push notifications via ntfy.sh."
    )
    parser.add_argument(
        "--workspace-path",
        default=None,
        help="Explicit path to the .cobots/ workspace directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- send --
    send_parser = subparsers.add_parser(
        "send",
        help="Publish a notification.",
    )
    send_parser.add_argument(
        "--message", "-m",
        default=None,
        help="Message body. If omitted, reads from STDIN.",
    )
    send_parser.add_argument(
        "--title", "-t",
        default=None,
        help="Optional notification title.",
    )
    send_parser.add_argument(
        "--priority", "-p",
        default=None,
        help="Priority: 1-5 or name (min, low, default, high, max, urgent).",
    )
    send_parser.add_argument(
        "--tags",
        default=None,
        help="Comma-separated list of tags.",
    )
    send_parser.add_argument(
        "--click",
        default=None,
        help="URL to open when notification is clicked.",
    )
    send_parser.add_argument(
        "--markdown",
        action="store_true",
        help="Enable Markdown rendering for the message.",
    )
    send_parser.add_argument(
        "--topic",
        default=None,
        help="Override the topic from config.",
    )
    send_parser.add_argument(
        "--url",
        default=None,
        help="Override the server URL from config.",
    )
    send_parser.add_argument(
        "--token",
        default=None,
        help="Override the auth token from config.",
    )

    # -- test --
    test_parser = subparsers.add_parser(
        "test",
        help="Send a test notification.",
    )
    test_parser.add_argument(
        "--topic",
        default=None,
        help="Override the topic from config.",
    )
    test_parser.add_argument(
        "--url",
        default=None,
        help="Override the server URL from config.",
    )
    test_parser.add_argument(
        "--token",
        default=None,
        help="Override the auth token from config.",
    )

    # -- show-config --
    subparsers.add_parser(
        "show-config",
        help="Display current ntfy configuration.",
    )

    args = parser.parse_args()

    # Load workspace configuration.
    config = load_config(args.workspace_path)

    handlers = {
        "send": cmd_send,
        "test": cmd_test,
        "show-config": cmd_show_config,
    }

    return handlers[args.command](args, config)


if __name__ == "__main__":
    sys.exit(main())
