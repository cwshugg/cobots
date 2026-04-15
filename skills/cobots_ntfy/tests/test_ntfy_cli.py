"""
test_ntfy_cli.py - Unit tests for the ntfy CLI (ntfy-cli.py).

Tests the CLI's subcommands (send, test, show-config), argument parsing,
priority resolution, token masking, and error handling. Network calls are
mocked so tests run offline and deterministically.
"""

import argparse
import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib and the CLI module are importable.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

# We need to import the CLI module. Since it uses a bootstrap pattern with
# sys.path manipulation and venv activation that has already run, we can
# import the helper functions and command handlers directly.
_CLI_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _CLI_DIR not in sys.path:
    sys.path.insert(0, _CLI_DIR)

# Patch venv activation before importing the CLI module.
sys.modules.setdefault("venv", MagicMock())
sys.modules.setdefault("venv.venv", MagicMock())

# Import after patching.
import importlib
ntfy_cli = importlib.import_module("ntfy-cli")

from cobots_lib.ntfy.client import NtfyResponse, PRIORITY_NAMES
from cobots_lib.workspace.config import CobotsConfig, NtfyConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    url: str = "https://ntfy.sh",
    topic: str = "test-topic",
    token: str = "",
    mode: str = "open",
    confidential_messages: list[dict] | None = None,
    confidential_titles: list[dict] | None = None,
) -> CobotsConfig:
    """Creates a CobotsConfig with the given ntfy settings."""
    return CobotsConfig(
        ntfy=NtfyConfig(
            url=url,
            topic=topic,
            token=token,
            mode=mode,
            confidential_messages=confidential_messages,
            confidential_titles=confidential_titles,
        ),
    )


def _make_send_args(**kwargs) -> argparse.Namespace:
    """Creates a Namespace mimicking parsed ``send`` subcommand args."""
    defaults = {
        "command": "send",
        "message": None,
        "title": None,
        "priority": None,
        "tags": None,
        "click": None,
        "markdown": False,
        "topic": None,
        "url": None,
        "token": None,
        "workspace_path": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_test_args(**kwargs) -> argparse.Namespace:
    """Creates a Namespace mimicking parsed ``test`` subcommand args."""
    defaults = {
        "command": "test",
        "topic": None,
        "url": None,
        "token": None,
        "workspace_path": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_show_config_args(**kwargs) -> argparse.Namespace:
    """Creates a Namespace mimicking parsed ``show-config`` subcommand args."""
    defaults = {
        "command": "show-config",
        "workspace_path": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Tests: resolve_priority
# ---------------------------------------------------------------------------


class TestResolvePriority(unittest.TestCase):
    """Tests for the ``resolve_priority()`` helper function."""

    def test_numeric_string_valid(self) -> None:
        """Numeric strings 1–5 resolve to their integer values."""
        for i in range(1, 6):
            self.assertEqual(ntfy_cli.resolve_priority(str(i)), i)

    def test_named_priorities(self) -> None:
        """All named priorities resolve correctly."""
        for name, expected in PRIORITY_NAMES.items():
            self.assertEqual(ntfy_cli.resolve_priority(name), expected)

    def test_named_priority_case_insensitive(self) -> None:
        """Priority names are case-insensitive."""
        self.assertEqual(ntfy_cli.resolve_priority("HIGH"), 4)
        self.assertEqual(ntfy_cli.resolve_priority("Max"), 5)
        self.assertEqual(ntfy_cli.resolve_priority("LOW"), 2)

    def test_numeric_string_out_of_range(self) -> None:
        """Out-of-range numeric priority raises ValueError."""
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("0")
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("6")
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("99")

    def test_invalid_name(self) -> None:
        """An unrecognized name raises ValueError."""
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("critical")
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("foobar")

    def test_negative_number(self) -> None:
        """Negative numbers raise ValueError."""
        with self.assertRaises(ValueError):
            ntfy_cli.resolve_priority("-1")

    def test_urgent_maps_to_max(self) -> None:
        """'urgent' is an alias for max priority (5)."""
        self.assertEqual(ntfy_cli.resolve_priority("urgent"), 5)


# ---------------------------------------------------------------------------
# Tests: mask_token
# ---------------------------------------------------------------------------


class TestMaskToken(unittest.TestCase):
    """Tests for the ``mask_token()`` helper function."""

    def test_empty_token(self) -> None:
        """An empty token returns '(not set)'."""
        self.assertEqual(ntfy_cli.mask_token(""), "(not set)")

    def test_short_token(self) -> None:
        """A short token shows only '(set)' without revealing content."""
        self.assertEqual(ntfy_cli.mask_token("abc"), "(set)")

    def test_normal_token(self) -> None:
        """A typical token shows first 5 chars + '... (set)'."""
        self.assertEqual(
            ntfy_cli.mask_token("tk_AgXXXXXXXXXXXX"),
            "tk_Ag... (set)",
        )

    def test_exact_five_chars(self) -> None:
        """A 5-char token shows only '(set)' (too short to safely reveal)."""
        self.assertEqual(ntfy_cli.mask_token("12345"), "(set)")


# ---------------------------------------------------------------------------
# Tests: build_client
# ---------------------------------------------------------------------------


class TestBuildClient(unittest.TestCase):
    """Tests for the ``build_client()`` helper function."""

    def test_uses_config_defaults(self) -> None:
        """Client uses config values when no CLI overrides are provided."""
        config = _make_config(
            url="https://my-ntfy.example.com",
            topic="my-topic",
            token="tk_secret",
        )
        args = _make_send_args()
        client = ntfy_cli.build_client(config, args)
        self.assertEqual(client._url, "https://my-ntfy.example.com")
        self.assertEqual(client._topic, "my-topic")
        self.assertEqual(client._token, "tk_secret")

    def test_cli_overrides_take_precedence(self) -> None:
        """CLI arguments override config values."""
        config = _make_config(
            url="https://ntfy.sh",
            topic="config-topic",
            token="config-token",
        )
        args = _make_send_args(
            url="https://override.example.com",
            topic="override-topic",
            token="override-token",
        )
        client = ntfy_cli.build_client(config, args)
        self.assertEqual(client._url, "https://override.example.com")
        self.assertEqual(client._topic, "override-topic")
        self.assertEqual(client._token, "override-token")

    def test_empty_topic_raises(self) -> None:
        """An empty topic (config + no override) raises ValueError."""
        config = _make_config(topic="")
        args = _make_send_args()
        with self.assertRaises(ValueError):
            ntfy_cli.build_client(config, args)


# ---------------------------------------------------------------------------
# Tests: cmd_send
# ---------------------------------------------------------------------------


class TestCmdSend(unittest.TestCase):
    """Tests for the ``cmd_send()`` command handler."""

    def test_send_success_with_message_flag(self) -> None:
        """Successful send with --message prints 'Sent: <id>'."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message="Hello world")

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="msg123"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        self.assertEqual(mock_out.getvalue().strip(), "Sent: msg123")
        mock_client.send.assert_called_once_with(
            "Hello world",
            title=None,
            priority=None,
            tags=None,
            click=None,
            markdown=False,
        )

    def test_send_success_with_all_options(self) -> None:
        """Send passes all options to the client correctly."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(
            message="Alert!",
            title="Urgent Alert",
            priority="4",
            tags="warning,alert",
            click="https://example.com",
            markdown=True,
        )

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="msg456"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("sys.stdout", new_callable=io.StringIO):
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        mock_client.send.assert_called_once_with(
            "Alert!",
            title="Urgent Alert",
            priority=4,
            tags=["warning", "alert"],
            click="https://example.com",
            markdown=True,
        )

    def test_send_reads_from_stdin(self) -> None:
        """When --message is omitted, message is read from STDIN."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message=None)

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="stdin_msg"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdin",
                new=io.StringIO("Message from stdin\n"),
            ):
                with patch(
                    "sys.stdin.isatty", return_value=False
                ):
                    with patch(
                        "sys.stdout", new_callable=io.StringIO
                    ) as mock_out:
                        result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        self.assertIn("Sent: stdin_msg", mock_out.getvalue())

    def test_send_no_message_error(self) -> None:
        """No message from --message or STDIN exits with error."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message=None)

        with patch("sys.stdin", new=io.StringIO("")):
            with patch("sys.stdin.isatty", return_value=False):
                with patch(
                    "sys.stderr", new_callable=io.StringIO
                ) as mock_err:
                    result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("message is required", mock_err.getvalue())

    def test_send_invalid_priority_error(self) -> None:
        """Invalid priority string exits with error."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message="Hello", priority="invalid")

        with patch("sys.stderr", new_callable=io.StringIO) as mock_err:
            result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("invalid priority", mock_err.getvalue())

    def test_send_failure_response(self) -> None:
        """A failed send prints error to stderr and exits 1."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message="Hello")

        mock_response = NtfyResponse(
            success=False, status_code=403, error="not authorized"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error: not authorized", mock_err.getvalue())

    def test_send_named_priority(self) -> None:
        """Named priorities (e.g. 'high') are resolved to integers."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message="Hello", priority="high")

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="prio_msg"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("sys.stdout", new_callable=io.StringIO):
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        call_kwargs = mock_client.send.call_args
        self.assertEqual(call_kwargs.kwargs["priority"], 4)

    def test_send_build_client_error(self) -> None:
        """ValueError from build_client is caught and printed."""
        config = _make_config(topic="")
        args = _make_send_args(message="Hello")

        with patch(
            "sys.stderr", new_callable=io.StringIO
        ) as mock_err:
            result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error:", mock_err.getvalue())

    def test_send_client_send_valueerror(self) -> None:
        """ValueError from client.send() is caught and printed."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(message="Hello")

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.side_effect = ValueError("bad message")
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error: bad message", mock_err.getvalue())

    def test_send_tags_parsed_correctly(self) -> None:
        """Comma-separated tags are split and trimmed."""
        config = _make_config(topic="test-topic")
        args = _make_send_args(
            message="Hello", tags="  tada , rocket , fire  "
        )

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="tag_msg"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("sys.stdout", new_callable=io.StringIO):
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        call_kwargs = mock_client.send.call_args
        self.assertEqual(
            call_kwargs.kwargs["tags"], ["tada", "rocket", "fire"]
        )


# ---------------------------------------------------------------------------
# Tests: cmd_test
# ---------------------------------------------------------------------------


class TestCmdTest(unittest.TestCase):
    """Tests for the ``cmd_test()`` command handler."""

    def test_test_success(self) -> None:
        """Successful test notification prints 'Sent: <id>'."""
        config = _make_config(topic="test-topic")
        args = _make_test_args()

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="test_msg"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 0)
        self.assertIn("Sent: test_msg", mock_out.getvalue())

        # Verify the test notification content.
        mock_client.send.assert_called_once_with(
            "Cobots ntfy test notification",
            title="Cobots Test",
            tags=["white_check_mark"],
        )

    def test_test_failure(self) -> None:
        """Failed test notification prints error to stderr."""
        config = _make_config(topic="test-topic")
        args = _make_test_args()

        mock_response = NtfyResponse(
            success=False, status_code=500, error="server error"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error: server error", mock_err.getvalue())

    def test_test_with_overrides(self) -> None:
        """CLI overrides are passed to build_client."""
        config = _make_config(topic="test-topic")
        args = _make_test_args(
            topic="override-topic",
            url="https://override.example.com",
            token="override-token",
        )

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="override_msg"
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch("sys.stdout", new_callable=io.StringIO):
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 0)
        mock_build.assert_called_once_with(config, args)

    def test_test_empty_topic_error(self) -> None:
        """Test with no topic configured exits with error."""
        config = _make_config(topic="")
        args = _make_test_args()

        with patch(
            "sys.stderr", new_callable=io.StringIO
        ) as mock_err:
            result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error:", mock_err.getvalue())

    def test_test_valueerror_from_send(self) -> None:
        """ValueError from client.send() during test is handled."""
        config = _make_config(topic="test-topic")
        args = _make_test_args()

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.side_effect = ValueError("send failed")
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 1)
        self.assertIn("Error: send failed", mock_err.getvalue())


# ---------------------------------------------------------------------------
# Tests: cmd_show_config
# ---------------------------------------------------------------------------


class TestCmdShowConfig(unittest.TestCase):
    """Tests for the ``cmd_show_config()`` command handler."""

    def test_show_config_with_all_fields(self) -> None:
        """Shows url, topic, and masked token."""
        config = _make_config(
            url="https://ntfy.sh",
            topic="my-cobots-topic",
            token="tk_AgXXXXXXXXXXXX",
        )
        args = _make_show_config_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_show_config(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("ntfy configuration:", output)
        self.assertIn("url:   https://ntfy.sh", output)
        self.assertIn("topic: my-cobots-topic", output)
        self.assertIn("token: tk_Ag... (set)", output)

    def test_show_config_no_token(self) -> None:
        """Shows '(not set)' when token is empty."""
        config = _make_config(
            url="https://ntfy.sh",
            topic="my-topic",
            token="",
        )
        args = _make_show_config_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_show_config(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("token: (not set)", output)

    def test_show_config_no_topic(self) -> None:
        """Shows '(not set)' when topic is empty."""
        config = _make_config(url="https://ntfy.sh", topic="", token="")
        args = _make_show_config_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_show_config(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("topic: (not set)", output)

    def test_show_config_returns_zero(self) -> None:
        """show-config always returns 0."""
        config = _make_config()
        args = _make_show_config_args()

        with patch("sys.stdout", new_callable=io.StringIO):
            result = ntfy_cli.cmd_show_config(args, config)

        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Tests: main() argument parsing (integration-style)
# ---------------------------------------------------------------------------


class TestMainArgParsing(unittest.TestCase):
    """Tests for ``main()`` argument parsing and dispatch."""

    @patch.object(ntfy_cli, "load_config")
    def test_no_subcommand_exits_with_error(self, mock_load) -> None:
        """Calling with no subcommand exits with error."""
        with patch("sys.argv", ["ntfy-cli.py"]):
            with self.assertRaises(SystemExit) as ctx:
                ntfy_cli.main()
            self.assertNotEqual(ctx.exception.code, 0)

    @patch.object(ntfy_cli, "load_config")
    def test_show_config_dispatches(self, mock_load) -> None:
        """'show-config' subcommand dispatches correctly."""
        mock_load.return_value = _make_config(topic="dispatch-topic")

        with patch("sys.argv", ["ntfy-cli.py", "show-config"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
                result = ntfy_cli.main()

        self.assertEqual(result, 0)
        self.assertIn("dispatch-topic", mock_out.getvalue())

    @patch.object(ntfy_cli, "load_config")
    def test_workspace_path_passed_to_load_config(self, mock_load) -> None:
        """--workspace-path is forwarded to load_config."""
        mock_load.return_value = _make_config()

        with patch(
            "sys.argv",
            ["ntfy-cli.py", "--workspace-path", "/tmp/test", "show-config"],
        ):
            with patch("sys.stdout", new_callable=io.StringIO):
                ntfy_cli.main()

        mock_load.assert_called_once_with("/tmp/test")


# ---------------------------------------------------------------------------
# Tests: Finding fixes (review report b8177a998be15dae)
# ---------------------------------------------------------------------------


class TestResolvePriorityControlFlow(unittest.TestCase):
    """Tests for Finding 1: resolve_priority() control flow fix.

    Verifies that out-of-range numeric priorities produce a specific
    error message (not the generic named-alternatives message).
    """

    def test_out_of_range_gives_specific_message(self) -> None:
        """Priority '6' should mention 'must be 1–5' without names."""
        with self.assertRaises(ValueError) as ctx:
            ntfy_cli.resolve_priority("6")
        msg = str(ctx.exception)
        self.assertIn("must be 1–5", msg)
        # Must NOT suggest named alternatives for a numeric input.
        self.assertNotIn("one of", msg)

    def test_out_of_range_zero(self) -> None:
        """Priority '0' gives a specific numeric error."""
        with self.assertRaises(ValueError) as ctx:
            ntfy_cli.resolve_priority("0")
        msg = str(ctx.exception)
        self.assertIn("must be 1–5", msg)
        self.assertNotIn("one of", msg)

    def test_out_of_range_negative(self) -> None:
        """Priority '-1' gives a specific numeric error."""
        with self.assertRaises(ValueError) as ctx:
            ntfy_cli.resolve_priority("-1")
        msg = str(ctx.exception)
        self.assertIn("must be 1–5", msg)
        self.assertNotIn("one of", msg)

    def test_out_of_range_large(self) -> None:
        """Priority '99' gives a specific numeric error."""
        with self.assertRaises(ValueError) as ctx:
            ntfy_cli.resolve_priority("99")
        msg = str(ctx.exception)
        self.assertIn("must be 1–5", msg)
        self.assertNotIn("one of", msg)

    def test_non_numeric_still_suggests_names(self) -> None:
        """Non-numeric invalid priority should suggest named alternatives."""
        with self.assertRaises(ValueError) as ctx:
            ntfy_cli.resolve_priority("foobar")
        msg = str(ctx.exception)
        self.assertIn("one of", msg)


class TestMaskTokenShortTokenSecurity(unittest.TestCase):
    """Tests for Finding 8: mask_token() short token security fix.

    Tokens shorter than 6 chars must show only '(set)'.
    """

    def test_single_char_token(self) -> None:
        """A 1-char token should return '(set)'."""
        self.assertEqual(ntfy_cli.mask_token("a"), "(set)")

    def test_five_char_token(self) -> None:
        """A 5-char token should return '(set)'."""
        self.assertEqual(ntfy_cli.mask_token("abcde"), "(set)")

    def test_six_char_token_shows_prefix(self) -> None:
        """A 6-char token should show first 5 chars."""
        self.assertEqual(ntfy_cli.mask_token("abcdef"), "abcde... (set)")


class TestReprTokenMasking(unittest.TestCase):
    """Tests for Finding 2: token must not appear in __repr__.

    Both NtfyConfig.__repr__ and CobotsConfig.__repr__ must mask
    the token when it is non-empty.
    """

    def test_ntfy_config_repr_masks_token(self) -> None:
        """NtfyConfig repr must not contain the raw token."""
        cfg = NtfyConfig(token="tk_secret_value_123")
        r = repr(cfg)
        self.assertNotIn("tk_secret_value_123", r)
        self.assertIn("***", r)

    def test_ntfy_config_repr_empty_token_no_mask(self) -> None:
        """NtfyConfig repr with empty token shows empty string."""
        cfg = NtfyConfig(token="")
        r = repr(cfg)
        self.assertNotIn("***", r)

    def test_cobots_config_repr_masks_token(self) -> None:
        """CobotsConfig repr must not contain the raw token."""
        ntfy = NtfyConfig(token="tk_top_secret_456")
        cfg = CobotsConfig(ntfy=ntfy)
        r = repr(cfg)
        self.assertNotIn("tk_top_secret_456", r)
        self.assertIn("***", r)

    def test_cobots_config_repr_empty_token_no_mask(self) -> None:
        """CobotsConfig repr with empty token shows empty string."""
        cfg = CobotsConfig(ntfy=NtfyConfig(token=""))
        r = repr(cfg)
        self.assertNotIn("***", r)


# ---------------------------------------------------------------------------
# Tests: NtfyConfig mode field
# ---------------------------------------------------------------------------


class TestNtfyConfigMode(unittest.TestCase):
    """Tests for the ``mode`` field on `NtfyConfig`."""

    def test_default_mode_is_confidential(self) -> None:
        """Default mode should be 'confidential'."""
        cfg = NtfyConfig()
        self.assertEqual(cfg.mode, "confidential")

    def test_valid_modes_accepted(self) -> None:
        """All three valid modes should be accepted."""
        for mode in ("open", "confidential", "closed"):
            cfg = NtfyConfig(mode=mode)
            self.assertEqual(cfg.mode, mode)

    def test_invalid_mode_raises(self) -> None:
        """An invalid mode string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            NtfyConfig(mode="quiet")
        self.assertIn("invalid ntfy mode", str(ctx.exception))

    def test_mode_in_to_dict(self) -> None:
        """``to_dict`` should include the mode field."""
        cfg = NtfyConfig(mode="open")
        d = cfg.to_dict()
        self.assertEqual(d["mode"], "open")

    def test_mode_from_dict(self) -> None:
        """``from_dict`` should read the mode field."""
        cfg = NtfyConfig.from_dict({"mode": "closed"})
        self.assertEqual(cfg.mode, "closed")

    def test_mode_from_dict_default(self) -> None:
        """``from_dict`` with no mode uses the default."""
        cfg = NtfyConfig.from_dict({})
        self.assertEqual(cfg.mode, "confidential")


class TestNtfyConfigConfidentialMessages(unittest.TestCase):
    """Tests for the ``confidential_messages`` field on `NtfyConfig`."""

    def test_default_is_none(self) -> None:
        """Default confidential_messages should be None."""
        cfg = NtfyConfig()
        self.assertIsNone(cfg.confidential_messages)

    def test_custom_messages_stored(self) -> None:
        """Custom messages are stored correctly."""
        msgs = [{"key": "a", "message": "Alpha"}]
        cfg = NtfyConfig(confidential_messages=msgs)
        self.assertEqual(cfg.confidential_messages, msgs)

    def test_to_dict_includes_when_set(self) -> None:
        """``to_dict`` includes confidential_messages when not None."""
        msgs = [{"key": "a", "message": "Alpha"}]
        cfg = NtfyConfig(confidential_messages=msgs)
        d = cfg.to_dict()
        self.assertIn("confidential_messages", d)
        self.assertEqual(d["confidential_messages"], msgs)

    def test_to_dict_excludes_when_none(self) -> None:
        """``to_dict`` omits confidential_messages when None."""
        cfg = NtfyConfig()
        d = cfg.to_dict()
        self.assertNotIn("confidential_messages", d)

    def test_from_dict_with_messages(self) -> None:
        """``from_dict`` reads confidential_messages."""
        data = {
            "confidential_messages": [
                {"key": "x", "message": "Xray"},
            ],
        }
        cfg = NtfyConfig.from_dict(data)
        self.assertEqual(
            cfg.confidential_messages,
            [{"key": "x", "message": "Xray"}],
        )

    def test_from_dict_without_messages(self) -> None:
        """``from_dict`` without confidential_messages gives None."""
        cfg = NtfyConfig.from_dict({})
        self.assertIsNone(cfg.confidential_messages)


# ---------------------------------------------------------------------------
# Tests: show-config displays mode
# ---------------------------------------------------------------------------


class TestCmdShowConfigMode(unittest.TestCase):
    """Tests for ``show-config`` displaying the mode field."""

    def test_show_config_displays_mode(self) -> None:
        """show-config should display the current mode."""
        config = _make_config(mode="confidential")
        args = _make_show_config_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_show_config(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("mode:  confidential", output)

    def test_show_config_displays_open_mode(self) -> None:
        """show-config should display 'open' mode."""
        config = _make_config(mode="open")
        args = _make_show_config_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            ntfy_cli.cmd_show_config(args, config)

        self.assertIn("mode:  open", mock_out.getvalue())


# ---------------------------------------------------------------------------
# Tests: list-messages subcommand
# ---------------------------------------------------------------------------


def _make_list_messages_args(**kwargs) -> argparse.Namespace:
    """Creates a Namespace mimicking parsed ``list-messages`` args."""
    defaults = {
        "command": "list-messages",
        "workspace_path": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCmdListMessages(unittest.TestCase):
    """Tests for the ``cmd_list_messages()`` command handler."""

    def test_lists_default_messages(self) -> None:
        """list-messages shows default predefined messages."""
        config = _make_config()
        args = _make_list_messages_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_list_messages(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("Available message keys:", output)
        self.assertIn("task_done", output)
        self.assertIn("A task has been completed", output)

    def test_lists_custom_messages(self) -> None:
        """list-messages shows custom messages from config."""
        config = _make_config(
            confidential_messages=[
                {"key": "custom_a", "message": "Custom Alpha"},
                {"key": "custom_b", "message": "Custom Beta"},
            ],
        )
        args = _make_list_messages_args()

        with patch(
            "sys.stdout", new_callable=io.StringIO
        ) as mock_out:
            result = ntfy_cli.cmd_list_messages(args, config)

        self.assertEqual(result, 0)
        output = mock_out.getvalue()
        self.assertIn("custom_a", output)
        self.assertIn("Custom Alpha", output)
        self.assertIn("custom_b", output)
        self.assertIn("Custom Beta", output)
        # Default keys should NOT be present.
        self.assertNotIn("task_done", output)

    def test_returns_zero(self) -> None:
        """list-messages always returns 0."""
        config = _make_config()
        args = _make_list_messages_args()

        with patch("sys.stdout", new_callable=io.StringIO):
            result = ntfy_cli.cmd_list_messages(args, config)

        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Tests: cmd_send with modes
# ---------------------------------------------------------------------------


class TestCmdSendConfidentialMode(unittest.TestCase):
    """Tests for ``cmd_send()`` in confidential mode."""

    def test_valid_key_sends_successfully(self) -> None:
        """Confidential mode: valid key sends the resolved message."""
        config = _make_config(mode="confidential", topic="test-topic")
        args = _make_send_args(message="task_done")

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="conf_msg",
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        self.assertIn("Sent: conf_msg", mock_out.getvalue())

    def test_invalid_key_shows_available_keys(self) -> None:
        """Invalid key in confidential mode prints available keys."""
        config = _make_config(mode="confidential", topic="test-topic")
        args = _make_send_args(message="not_a_valid_key")

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.side_effect = ValueError(
                "unknown message key 'not_a_valid_key'"
            )
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        output = mock_err.getvalue()
        self.assertIn("Error:", output)
        self.assertIn("Available message keys:", output)
        self.assertIn("task_done", output)
        self.assertIn("build_done", output)

    def test_invalid_key_with_custom_messages(self) -> None:
        """Invalid key shows custom messages when configured."""
        config = _make_config(
            mode="confidential",
            topic="test-topic",
            confidential_messages=[
                {"key": "my_key", "message": "My message"},
            ],
        )
        args = _make_send_args(message="wrong_key")

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.side_effect = ValueError(
                "unknown message key 'wrong_key'"
            )
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        output = mock_err.getvalue()
        self.assertIn("my_key", output)
        self.assertIn("My message", output)
        # Default keys should NOT appear.
        self.assertNotIn("task_done", output)


class TestCmdSendClosedMode(unittest.TestCase):
    """Tests for ``cmd_send()`` in closed mode."""

    def test_closed_mode_send_returns_error(self) -> None:
        """Closed mode: send returns error without HTTP request."""
        config = _make_config(mode="closed", topic="test-topic")
        args = _make_send_args(message="task_done")

        mock_response = NtfyResponse(
            success=False,
            status_code=0,
            error="notifications are disabled (mode=closed)",
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stderr", new_callable=io.StringIO
            ) as mock_err:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 1)
        self.assertIn("mode=closed", mock_err.getvalue())


class TestCmdSendOpenMode(unittest.TestCase):
    """Tests for ``cmd_send()`` in open mode."""

    def test_open_mode_freeform_message(self) -> None:
        """Open mode: free-form messages are allowed."""
        config = _make_config(mode="open", topic="test-topic")
        args = _make_send_args(message="Any free-form text")

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="open_msg",
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.cmd_send(args, config)

        self.assertEqual(result, 0)
        self.assertIn("Sent: open_msg", mock_out.getvalue())


# ---------------------------------------------------------------------------
# Tests: cmd_test with modes
# ---------------------------------------------------------------------------


class TestCmdTestWithModes(unittest.TestCase):
    """Tests for ``cmd_test()`` with different modes."""

    def test_test_closed_mode_refused(self) -> None:
        """Test subcommand in closed mode exits with error."""
        config = _make_config(mode="closed", topic="test-topic")
        args = _make_test_args()

        with patch(
            "sys.stderr", new_callable=io.StringIO
        ) as mock_err:
            result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 1)
        self.assertIn("mode=closed", mock_err.getvalue())

    def test_test_open_mode_sends_freeform(self) -> None:
        """Test in open mode sends the free-form test message."""
        config = _make_config(mode="open", topic="test-topic")
        args = _make_test_args()

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="test_open",
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 0)
        mock_client.send.assert_called_once_with(
            "Cobots ntfy test notification",
            title="Cobots Test",
            tags=["white_check_mark"],
        )

    def test_test_confidential_mode_uses_key(self) -> None:
        """Test in confidential mode sends a predefined key."""
        config = _make_config(
            mode="confidential", topic="test-topic",
        )
        args = _make_test_args()

        mock_response = NtfyResponse(
            success=True, status_code=200, message_id="test_conf",
        )

        with patch.object(
            ntfy_cli, "build_client"
        ) as mock_build:
            mock_client = MagicMock()
            mock_client.send.return_value = mock_response
            mock_build.return_value = mock_client

            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.cmd_test(args, config)

        self.assertEqual(result, 0)
        mock_client.send.assert_called_once_with(
            "task_done",
            title="task_update",
            tags=["white_check_mark"],
        )


# ---------------------------------------------------------------------------
# Tests: main() dispatches list-messages
# ---------------------------------------------------------------------------


class TestMainListMessagesDispatch(unittest.TestCase):
    """Tests for ``main()`` dispatching the list-messages subcommand."""

    @patch.object(ntfy_cli, "load_config")
    def test_list_messages_dispatches(self, mock_load) -> None:
        """'list-messages' subcommand dispatches correctly."""
        mock_load.return_value = _make_config()

        with patch(
            "sys.argv", ["ntfy-cli.py", "list-messages"]
        ):
            with patch(
                "sys.stdout", new_callable=io.StringIO
            ) as mock_out:
                result = ntfy_cli.main()

        self.assertEqual(result, 0)
        self.assertIn("Available message keys:", mock_out.getvalue())


if __name__ == "__main__":
    unittest.main()
