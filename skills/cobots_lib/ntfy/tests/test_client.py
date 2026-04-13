"""
test_client.py - Unit tests for the ntfy notification client.

Tests constants, `NtfyResponse`, `NtfyClient`, and `send_notification()`.
Network calls are mocked with `unittest.mock.patch` so tests run
offline and deterministically.
"""

import http.client
import io
import json
import os
import socket
import sys
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib is importable regardless of working directory.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.ntfy.client import (
    DEFAULT_TIMEOUT,
    PRIORITY_DEFAULT,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MAX,
    PRIORITY_MIN,
    PRIORITY_NAMES,
    VALID_PRIORITIES,
    NtfyClient,
    NtfyResponse,
    send_notification,
)
from cobots_lib.workspace.config import CobotsConfig, NtfyConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_success_response(
    message_id: str = "abc123",
    topic: str = "test-topic",
) -> MagicMock:
    """Creates a mock `http.client.HTTPResponse` for a successful publish."""
    body = json.dumps({
        "id": message_id,
        "time": 1234567890,
        "expires": 1234654290,
        "event": "message",
        "topic": topic,
        "message": "test",
    }).encode("utf-8")
    resp = MagicMock()
    resp.status = 200
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_error_response(
    code: int = 403,
    error_msg: str = "forbidden",
) -> "urllib.error.HTTPError":
    """Creates an `HTTPError` with a JSON body."""
    import urllib.error

    body = json.dumps({
        "code": code,
        "http": code,
        "error": error_msg,
        "link": "https://ntfy.sh/docs",
    }).encode("utf-8")
    err = urllib.error.HTTPError(
        url="https://ntfy.sh/test-topic",
        code=code,
        msg=error_msg,
        hdrs={},
        fp=io.BytesIO(body),
    )
    return err


# ===================================================================
# Constants tests
# ===================================================================


class TestPriorityConstants(unittest.TestCase):
    """Verify the priority constants have the correct values."""

    def test_priority_min(self) -> None:
        self.assertEqual(PRIORITY_MIN, 1)

    def test_priority_low(self) -> None:
        self.assertEqual(PRIORITY_LOW, 2)

    def test_priority_default(self) -> None:
        self.assertEqual(PRIORITY_DEFAULT, 3)

    def test_priority_high(self) -> None:
        self.assertEqual(PRIORITY_HIGH, 4)

    def test_priority_max(self) -> None:
        self.assertEqual(PRIORITY_MAX, 5)


class TestValidPriorities(unittest.TestCase):
    """Verify `VALID_PRIORITIES` contains exactly the five levels."""

    def test_is_set(self) -> None:
        self.assertIsInstance(VALID_PRIORITIES, set)

    def test_contains_all_five(self) -> None:
        self.assertEqual(VALID_PRIORITIES, {1, 2, 3, 4, 5})


class TestPriorityNames(unittest.TestCase):
    """Verify the name-to-int mapping is correct."""

    def test_min(self) -> None:
        self.assertEqual(PRIORITY_NAMES["min"], 1)

    def test_low(self) -> None:
        self.assertEqual(PRIORITY_NAMES["low"], 2)

    def test_default(self) -> None:
        self.assertEqual(PRIORITY_NAMES["default"], 3)

    def test_high(self) -> None:
        self.assertEqual(PRIORITY_NAMES["high"], 4)

    def test_max(self) -> None:
        self.assertEqual(PRIORITY_NAMES["max"], 5)

    def test_urgent_is_alias_for_max(self) -> None:
        self.assertEqual(PRIORITY_NAMES["urgent"], 5)


class TestDefaultTimeout(unittest.TestCase):
    """Verify the default timeout constant."""

    def test_value(self) -> None:
        self.assertEqual(DEFAULT_TIMEOUT, 30)


# ===================================================================
# NtfyResponse tests
# ===================================================================


class TestNtfyResponseSuccess(unittest.TestCase):
    """Verify successful response objects."""

    def test_success_fields(self) -> None:
        resp = NtfyResponse(
            success=True,
            status_code=200,
            message_id="abc123",
            raw={"id": "abc123"},
        )
        self.assertTrue(resp.success)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.message_id, "abc123")
        self.assertIsNone(resp.error)
        self.assertEqual(resp.raw, {"id": "abc123"})


class TestNtfyResponseFailure(unittest.TestCase):
    """Verify failure response objects."""

    def test_failure_fields(self) -> None:
        resp = NtfyResponse(
            success=False,
            status_code=403,
            error="forbidden",
        )
        self.assertFalse(resp.success)
        self.assertEqual(resp.status_code, 403)
        self.assertIsNone(resp.message_id)
        self.assertEqual(resp.error, "forbidden")
        self.assertIsNone(resp.raw)


class TestNtfyResponseDefaults(unittest.TestCase):
    """Verify optional fields default to None."""

    def test_defaults(self) -> None:
        resp = NtfyResponse(success=True, status_code=200)
        self.assertIsNone(resp.message_id)
        self.assertIsNone(resp.error)
        self.assertIsNone(resp.raw)


class TestNtfyResponseRepr(unittest.TestCase):
    """Verify `__repr__` for readability."""

    def test_success_repr(self) -> None:
        resp = NtfyResponse(
            success=True, status_code=200, message_id="xyz",
        )
        r = repr(resp)
        self.assertIn("success=True", r)
        self.assertIn("xyz", r)

    def test_failure_repr(self) -> None:
        resp = NtfyResponse(
            success=False, status_code=500, error="server error",
        )
        r = repr(resp)
        self.assertIn("success=False", r)
        self.assertIn("server error", r)


# ===================================================================
# NtfyClient.__init__ tests
# ===================================================================


class TestNtfyClientInit(unittest.TestCase):
    """Verify constructor validation and field storage."""

    def test_valid_construction(self) -> None:
        client = NtfyClient(
            url="https://ntfy.sh",
            topic="test",
            token="tk_abc",
            timeout=10,
        )
        # Access private attrs to verify storage.
        self.assertEqual(client._url, "https://ntfy.sh")
        self.assertEqual(client._topic, "test")
        self.assertEqual(client._token, "tk_abc")
        self.assertEqual(client._timeout, 10)

    def test_trailing_slash_stripped(self) -> None:
        client = NtfyClient(url="https://ntfy.sh/", topic="t")
        self.assertEqual(client._url, "https://ntfy.sh")

    def test_empty_url_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            NtfyClient(url="", topic="test")
        self.assertIn("URL", str(ctx.exception))

    def test_none_url_raises(self) -> None:
        with self.assertRaises(ValueError):
            NtfyClient(url=None, topic="test")

    def test_whitespace_url_raises(self) -> None:
        with self.assertRaises(ValueError):
            NtfyClient(url="   ", topic="test")

    def test_empty_topic_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            NtfyClient(url="https://ntfy.sh", topic="")
        self.assertIn("topic", str(ctx.exception))

    def test_whitespace_topic_raises(self) -> None:
        with self.assertRaises(ValueError):
            NtfyClient(url="https://ntfy.sh", topic="   ")

    def test_default_token_is_empty(self) -> None:
        client = NtfyClient(url="https://ntfy.sh", topic="t")
        self.assertEqual(client._token, "")

    def test_default_timeout(self) -> None:
        client = NtfyClient(url="https://ntfy.sh", topic="t")
        self.assertEqual(client._timeout, DEFAULT_TIMEOUT)


# ===================================================================
# NtfyClient.from_config tests
# ===================================================================


class TestNtfyClientFromConfig(unittest.TestCase):
    """Verify the `from_config` class method."""

    def test_creates_client_from_config(self) -> None:
        ntfy_cfg = NtfyConfig(
            url="https://my-ntfy.example.com",
            topic="cobots",
            token="tk_secret",
        )
        config = CobotsConfig(ntfy=ntfy_cfg)
        client = NtfyClient.from_config(config)
        self.assertEqual(client._url, "https://my-ntfy.example.com")
        self.assertEqual(client._topic, "cobots")
        self.assertEqual(client._token, "tk_secret")

    def test_empty_topic_in_config_raises(self) -> None:
        config = CobotsConfig(ntfy=NtfyConfig(topic=""))
        with self.assertRaises(ValueError) as ctx:
            NtfyClient.from_config(config)
        self.assertIn("topic", str(ctx.exception))

    def test_default_config_raises_because_topic_empty(self) -> None:
        """Default CobotsConfig has an empty topic — should raise."""
        config = CobotsConfig()
        with self.assertRaises(ValueError):
            NtfyClient.from_config(config)


# ===================================================================
# NtfyClient.send — validation tests
# ===================================================================


class TestNtfyClientSendValidation(unittest.TestCase):
    """Verify `send()` validates inputs before making HTTP requests."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test-topic", mode="open",
        )

    def test_empty_message_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.send("")
        self.assertIn("message", str(ctx.exception))

    def test_whitespace_message_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.client.send("   ")

    def test_invalid_priority_too_high(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.client.send("test", priority=6)
        self.assertIn("priority", str(ctx.exception))

    def test_invalid_priority_zero(self) -> None:
        with self.assertRaises(ValueError):
            self.client.send("test", priority=0)

    def test_invalid_priority_negative(self) -> None:
        with self.assertRaises(ValueError):
            self.client.send("test", priority=-1)

    def test_invalid_url_scheme(self) -> None:
        """Client with a non-http(s) URL should raise on send."""
        client = NtfyClient.__new__(NtfyClient)
        client._url = "ftp://ntfy.sh"
        client._topic = "test"
        client._token = ""
        client._timeout = 30
        client._mode = "open"
        client._confidential_messages = {}
        with self.assertRaises(ValueError) as ctx:
            client.send("test")
        self.assertIn("http", str(ctx.exception))


# ===================================================================
# NtfyClient.send — HTTP success tests
# ===================================================================


class TestNtfyClientSendSuccess(unittest.TestCase):
    """Verify `send()` returns correct `NtfyResponse` on HTTP 200."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh",
            topic="test-topic",
            token="tk_abc",
            mode="open",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_basic_send(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response("msg001")

        result = self.client.send("Hello world")

        self.assertTrue(result.success)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.message_id, "msg001")
        self.assertIsNotNone(result.raw)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_request_url_is_correct(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://ntfy.sh/test-topic")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_request_method_is_post(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.method, "POST")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_request_body_is_utf8(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("héllo wörld")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.data, "héllo wörld".encode("utf-8"))

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_auth_header_set(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.get_header("Authorization"), "Bearer tk_abc",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_no_auth_header_when_token_empty(
        self, mock_urlopen: MagicMock,
    ) -> None:
        client = NtfyClient(url="https://ntfy.sh", topic="t", mode="open")
        mock_urlopen.return_value = _make_success_response()

        client.send("test")

        req = mock_urlopen.call_args[0][0]
        self.assertIsNone(req.get_header("Authorization"))

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_title_header(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test", title="My Title")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Title"), "My Title")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_priority_header(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test", priority=4)

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Priority"), "4")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_tags_header_comma_joined(
        self, mock_urlopen: MagicMock,
    ) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test", tags=["warning", "robot"])

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Tags"), "warning,robot")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_click_header(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("test", click="https://example.com")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.get_header("Click"), "https://example.com",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_markdown_header(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("**bold**", markdown=True)

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Markdown"), "yes")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_no_markdown_header_when_false(
        self, mock_urlopen: MagicMock,
    ) -> None:
        mock_urlopen.return_value = _make_success_response()

        self.client.send("plain text", markdown=False)

        req = mock_urlopen.call_args[0][0]
        self.assertIsNone(req.get_header("Markdown"))

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_no_optional_headers_when_not_set(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """When optional params are omitted, their headers should not
        be present.
        """
        client = NtfyClient(url="https://ntfy.sh", topic="t", mode="open")
        mock_urlopen.return_value = _make_success_response()

        client.send("just a message")

        req = mock_urlopen.call_args[0][0]
        self.assertIsNone(req.get_header("Title"))
        self.assertIsNone(req.get_header("Priority"))
        self.assertIsNone(req.get_header("Tags"))
        self.assertIsNone(req.get_header("Click"))
        self.assertIsNone(req.get_header("Markdown"))
        self.assertIsNone(req.get_header("Authorization"))

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_timeout_passed_to_urlopen(
        self, mock_urlopen: MagicMock,
    ) -> None:
        client = NtfyClient(
            url="https://ntfy.sh", topic="t", timeout=42, mode="open",
        )
        mock_urlopen.return_value = _make_success_response()

        client.send("test")

        _, kwargs = mock_urlopen.call_args
        self.assertEqual(kwargs.get("timeout"), 42)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_all_valid_priorities_accepted(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """Each of the five valid priority values should work."""
        mock_urlopen.return_value = _make_success_response()

        for p in (1, 2, 3, 4, 5):
            result = self.client.send("test", priority=p)
            self.assertTrue(result.success, f"priority {p} failed")


# ===================================================================
# NtfyClient.send — HTTP error tests
# ===================================================================


class TestNtfyClientSendHTTPErrors(unittest.TestCase):
    """Verify `send()` captures HTTP errors in `NtfyResponse`."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test-topic", mode="open",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_http_403(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = _make_error_response(403, "forbidden")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 403)
        self.assertIn("forbidden", result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_http_429(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = _make_error_response(429, "rate limited")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 429)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_http_500(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = _make_error_response(500, "server error")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 500)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_http_error_with_non_json_body(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """If the error body is not JSON, we still get a response."""
        import urllib.error

        err = urllib.error.HTTPError(
            url="https://ntfy.sh/test",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=io.BytesIO(b"<html>Bad Gateway</html>"),
        )
        mock_urlopen.side_effect = err

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 502)
        self.assertIsNotNone(result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_http_error_raw_data_captured(
        self, mock_urlopen: MagicMock,
    ) -> None:
        mock_urlopen.side_effect = _make_error_response(403, "forbidden")

        result = self.client.send("test")

        self.assertIsNotNone(result.raw)
        self.assertEqual(result.raw.get("code"), 403)


# ===================================================================
# NtfyClient.send — network error tests
# ===================================================================


class TestNtfyClientSendNetworkErrors(unittest.TestCase):
    """Verify `send()` captures network errors without raising."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test-topic", mode="open",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_timeout(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = socket.timeout("timed out")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertIn("timed out", result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_connection_refused(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError(
            ConnectionRefusedError("Connection refused"),
        )

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertIn("network error", result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_dns_failure(self, mock_urlopen: MagicMock) -> None:
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError(
            socket.gaierror(8, "Name or service not known"),
        )

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertIn("network error", result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_generic_os_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = OSError("broken pipe")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertIn("broken pipe", result.error)

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_unexpected_exception(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = RuntimeError("something weird")

        result = self.client.send("test")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertIn("something weird", result.error)


# ===================================================================
# send_notification() convenience function tests
# ===================================================================


class TestSendNotification(unittest.TestCase):
    """Verify the `send_notification()` convenience function."""

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_sends_via_config(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response("conv001")

        config = CobotsConfig(
            ntfy=NtfyConfig(
                topic="my-topic", token="tk_test", mode="open",
            ),
        )
        result = send_notification(config, "Hello!")

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "conv001")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_passes_all_options(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _make_success_response()

        config = CobotsConfig(
            ntfy=NtfyConfig(topic="my-topic", mode="open"),
        )
        send_notification(
            config,
            "test",
            title="Title",
            priority=4,
            tags=["tag1"],
            click="https://example.com",
            markdown=True,
        )

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Title"), "Title")
        self.assertEqual(req.get_header("Priority"), "4")
        self.assertEqual(req.get_header("Tags"), "tag1")
        self.assertEqual(req.get_header("Click"), "https://example.com")
        self.assertEqual(req.get_header("Markdown"), "yes")

    def test_raises_on_empty_topic(self) -> None:
        config = CobotsConfig(ntfy=NtfyConfig(topic=""))
        with self.assertRaises(ValueError):
            send_notification(config, "test")

    def test_raises_on_empty_message(self) -> None:
        config = CobotsConfig(
            ntfy=NtfyConfig(topic="my-topic", mode="open"),
        )
        with self.assertRaises(ValueError):
            send_notification(config, "")


# ===================================================================
# Integration-style tests (verifying end-to-end flow with mocks)
# ===================================================================


class TestEndToEndFlow(unittest.TestCase):
    """Verify realistic usage patterns work as expected."""

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_from_config_then_send(self, mock_urlopen: MagicMock) -> None:
        """Mimics the usage pattern from the architecture section 10."""
        mock_urlopen.return_value = _make_success_response("e2e001")

        config = CobotsConfig(
            ntfy=NtfyConfig(
                url="https://self-hosted.example.com",
                topic="cobots-alerts",
                token="tk_production",
                mode="open",
            ),
        )
        client = NtfyClient.from_config(config)
        result = client.send(
            "Task completed!",
            title="Cobots",
            tags=["tada"],
        )

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "e2e001")

        # Verify the request was constructed correctly.
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.full_url,
            "https://self-hosted.example.com/cobots-alerts",
        )
        self.assertEqual(
            req.get_header("Authorization"), "Bearer tk_production",
        )
        self.assertEqual(req.get_header("Title"), "Cobots")
        self.assertEqual(req.get_header("Tags"), "tada")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_multiple_sends_on_same_client(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """A single client can send multiple messages."""
        mock_urlopen.return_value = _make_success_response()

        client = NtfyClient(
            url="https://ntfy.sh", topic="multi", mode="open",
        )

        r1 = client.send("first")
        r2 = client.send("second", priority=5)
        r3 = client.send("third", tags=["a", "b"])

        self.assertTrue(r1.success)
        self.assertTrue(r2.success)
        self.assertTrue(r3.success)
        self.assertEqual(mock_urlopen.call_count, 3)


# ===================================================================
# NtfyClient mode tests
# ===================================================================


class TestNtfyClientModeValidation(unittest.TestCase):
    """Verify mode validation in `NtfyClient.__init__`."""

    def test_valid_modes_accepted(self) -> None:
        """All three valid mode strings are accepted."""
        for mode in ("open", "confidential", "closed"):
            client = NtfyClient(
                url="https://ntfy.sh", topic="t", mode=mode,
            )
            self.assertEqual(client._mode, mode)

    def test_invalid_mode_raises(self) -> None:
        """An invalid mode string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            NtfyClient(
                url="https://ntfy.sh", topic="t", mode="silent",
            )
        self.assertIn("invalid ntfy mode", str(ctx.exception))

    def test_empty_mode_raises(self) -> None:
        """An empty mode string raises ValueError."""
        with self.assertRaises(ValueError):
            NtfyClient(
                url="https://ntfy.sh", topic="t", mode="",
            )

    def test_default_mode_is_confidential(self) -> None:
        """Default mode is 'confidential'."""
        client = NtfyClient(url="https://ntfy.sh", topic="t")
        self.assertEqual(client._mode, "confidential")


class TestNtfyClientOpenMode(unittest.TestCase):
    """Verify open mode allows any message."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test", mode="open",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_any_message_allowed(self, mock_urlopen: MagicMock) -> None:
        """Open mode accepts free-form text."""
        mock_urlopen.return_value = _make_success_response("open001")

        result = self.client.send("Any arbitrary message!")

        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "open001")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_predefined_key_also_sent_as_is(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """In open mode, a predefined key is sent as-is (not resolved)."""
        mock_urlopen.return_value = _make_success_response()

        self.client.send("task_done")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.data, b"task_done")


class TestNtfyClientConfidentialMode(unittest.TestCase):
    """Verify confidential mode restricts messages to predefined keys."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test", mode="confidential",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_valid_key_resolves_to_display_string(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """A valid predefined key is resolved to its display string."""
        mock_urlopen.return_value = _make_success_response("conf001")

        result = self.client.send("task_done")

        self.assertTrue(result.success)
        # The actual HTTP body should be the display string, not the key.
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.data, "A task has been completed".encode("utf-8"),
        )

    def test_invalid_key_raises_valueerror(self) -> None:
        """An unrecognized key raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.client.send("not_a_real_key")
        msg = str(ctx.exception)
        self.assertIn("unknown message key", msg)
        self.assertIn("not_a_real_key", msg)

    def test_invalid_key_lists_valid_keys(self) -> None:
        """ValueError from invalid key lists all valid keys."""
        with self.assertRaises(ValueError) as ctx:
            self.client.send("bogus_key")
        msg = str(ctx.exception)
        # Should mention at least some known keys.
        self.assertIn("task_done", msg)
        self.assertIn("build_done", msg)

    def test_freeform_text_rejected(self) -> None:
        """Free-form text that isn't a key is rejected."""
        with self.assertRaises(ValueError):
            self.client.send("This is a free-form message")

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_all_default_keys_work(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """Every default predefined key should send successfully."""
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        mock_urlopen.return_value = _make_success_response()
        for key in DEFAULT_CONFIDENTIAL_MESSAGES:
            result = self.client.send(key)
            self.assertTrue(result.success, f"key {key!r} failed")


class TestNtfyClientConfidentialCustomMessages(unittest.TestCase):
    """Verify custom confidential messages override defaults."""

    def setUp(self) -> None:
        self.custom = {
            "custom_one": "Custom message one",
            "custom_two": "Custom message two",
        }
        self.client = NtfyClient(
            url="https://ntfy.sh",
            topic="test",
            mode="confidential",
            confidential_messages=self.custom,
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_custom_key_works(self, mock_urlopen: MagicMock) -> None:
        """Custom keys are accepted."""
        mock_urlopen.return_value = _make_success_response()

        result = self.client.send("custom_one")

        self.assertTrue(result.success)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.data, b"Custom message one",
        )

    def test_default_key_rejected_with_custom(self) -> None:
        """When custom messages are provided, default keys are not valid."""
        with self.assertRaises(ValueError):
            self.client.send("task_done")


class TestNtfyClientClosedMode(unittest.TestCase):
    """Verify closed mode refuses all sends."""

    def setUp(self) -> None:
        self.client = NtfyClient(
            url="https://ntfy.sh", topic="test", mode="closed",
        )

    def test_send_returns_failure(self) -> None:
        """Closed mode returns failure without HTTP request."""
        result = self.client.send("task_done")

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertEqual(
            result.error, "notifications are disabled (mode=closed)",
        )

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_no_http_request_made(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """Closed mode should not make any HTTP requests."""
        self.client.send("any message")

        mock_urlopen.assert_not_called()

    def test_freeform_also_blocked(self) -> None:
        """Even free-form text is blocked in closed mode."""
        result = self.client.send("Any free-form message")
        self.assertFalse(result.success)
        self.assertIn("mode=closed", result.error)


class TestNtfyClientFromConfigWithMode(unittest.TestCase):
    """Verify `from_config` reads mode and confidential_messages."""

    def test_mode_read_from_config(self) -> None:
        """Mode is read from config."""
        config = CobotsConfig(
            ntfy=NtfyConfig(topic="t", mode="open"),
        )
        client = NtfyClient.from_config(config)
        self.assertEqual(client._mode, "open")

    def test_default_mode_from_config(self) -> None:
        """Default config mode is 'confidential'."""
        config = CobotsConfig(ntfy=NtfyConfig(topic="t"))
        client = NtfyClient.from_config(config)
        self.assertEqual(client._mode, "confidential")

    def test_custom_messages_from_config(self) -> None:
        """Custom messages from config are loaded into the client."""
        config = CobotsConfig(
            ntfy=NtfyConfig(
                topic="t",
                confidential_messages=[
                    {"key": "my_msg", "message": "My custom msg"},
                ],
            ),
        )
        client = NtfyClient.from_config(config)
        self.assertEqual(
            client._confidential_messages,
            {"my_msg": "My custom msg"},
        )

    def test_none_messages_uses_defaults(self) -> None:
        """None confidential_messages uses the hardcoded defaults."""
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        config = CobotsConfig(ntfy=NtfyConfig(topic="t"))
        client = NtfyClient.from_config(config)
        self.assertEqual(
            client._confidential_messages,
            DEFAULT_CONFIDENTIAL_MESSAGES,
        )


class TestSendNotificationWithMode(unittest.TestCase):
    """Verify `send_notification()` respects mode settings."""

    @patch("cobots_lib.ntfy.client.urllib.request.urlopen")
    def test_confidential_mode_with_valid_key(
        self, mock_urlopen: MagicMock,
    ) -> None:
        """Confidential mode: valid key sends the display string."""
        mock_urlopen.return_value = _make_success_response("sn001")

        config = CobotsConfig(
            ntfy=NtfyConfig(topic="t", mode="confidential"),
        )
        result = send_notification(config, "task_done")

        self.assertTrue(result.success)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(
            req.data, "A task has been completed".encode("utf-8"),
        )

    def test_closed_mode_returns_failure(self) -> None:
        """Closed mode: send_notification returns failure."""
        config = CobotsConfig(
            ntfy=NtfyConfig(topic="t", mode="closed"),
        )
        result = send_notification(config, "task_done")

        self.assertFalse(result.success)
        self.assertIn("mode=closed", result.error)


class TestDefaultConfidentialMessages(unittest.TestCase):
    """Verify the hardcoded default confidential messages."""

    def test_message_count(self) -> None:
        """Should have between 15 and 20 default messages."""
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        count = len(DEFAULT_CONFIDENTIAL_MESSAGES)
        self.assertGreaterEqual(count, 15)
        self.assertLessEqual(count, 20)

    def test_keys_are_snake_case(self) -> None:
        """All keys should be snake_case."""
        import re
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        pattern = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
        for key in DEFAULT_CONFIDENTIAL_MESSAGES:
            self.assertRegex(
                key, pattern,
                f"key {key!r} is not snake_case",
            )

    def test_values_are_nonempty_strings(self) -> None:
        """All display strings should be non-empty."""
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        for key, msg in DEFAULT_CONFIDENTIAL_MESSAGES.items():
            self.assertIsInstance(msg, str)
            self.assertTrue(
                msg.strip(),
                f"message for key {key!r} is empty",
            )

    def test_expected_keys_present(self) -> None:
        """Certain expected keys should be in the defaults."""
        from cobots_lib.ntfy.client import DEFAULT_CONFIDENTIAL_MESSAGES

        expected = [
            "task_started", "task_done", "task_blocked",
            "build_done", "build_failed",
            "tests_passed", "tests_failed",
            "review_requested", "review_done",
            "question_for_human",
            "deploy_done",
            "error_occurred",
            "waiting_for_input",
            "report_ready",
        ]
        for key in expected:
            self.assertIn(
                key, DEFAULT_CONFIDENTIAL_MESSAGES,
                f"expected key {key!r} not in defaults",
            )


if __name__ == "__main__":
    unittest.main()
