"""
client.py - ntfy notification client for the Cobots Collective.

Implements the `NtfyClient` class and `send_notification()` convenience
function for publishing messages to an ntfy.sh server. Uses only the
Python standard library (`urllib.request`) — no third-party HTTP
dependencies.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Priority constants
# ---------------------------------------------------------------------------

# Minimum priority — lowest urgency. Clients may choose not to alert.
PRIORITY_MIN = 1

# Low priority — below normal urgency.
PRIORITY_LOW = 2

# Default priority — normal urgency (ntfy server default).
PRIORITY_DEFAULT = 3

# High priority — elevated urgency.
PRIORITY_HIGH = 4

# Maximum priority — highest urgency.
PRIORITY_MAX = 5

# The complete set of valid priority integers.
VALID_PRIORITIES = {1, 2, 3, 4, 5}

# Mapping of human-readable priority names to their integer values.
# "urgent" is an alias for max priority.
PRIORITY_NAMES: dict[str, int] = {
    "min": 1,
    "low": 2,
    "default": 3,
    "high": 4,
    "max": 5,
    "urgent": 5,
}

# Default HTTP request timeout in seconds.
DEFAULT_TIMEOUT = 30


# ---------------------------------------------------------------------------
# NtfyResponse
# ---------------------------------------------------------------------------


class NtfyResponse:
    """Represents the result of an ntfy publish request.

    Every call to `NtfyClient.send()` returns an `NtfyResponse` regardless
    of success or failure — network and HTTP errors are captured here
    rather than raised as exceptions.
    """

    def __init__(
        self,
        success: bool,
        status_code: int,
        message_id: str | None = None,
        error: str | None = None,
        raw: dict | None = None,
    ) -> None:
        """Initializes the response.

        Args:
            success: Whether the publish succeeded (HTTP 200).
            status_code: The HTTP status code, or 0 for non-HTTP errors.
            message_id: The ntfy message ID on success.
            error: A human-readable error description on failure.
            raw: The full parsed JSON response body (when available).
        """
        self.success = success
        self.status_code = status_code
        self.message_id = message_id
        self.error = error
        self.raw = raw

    def __repr__(self) -> str:
        if self.success:
            return f"NtfyResponse(success=True, message_id={self.message_id!r})"
        return f"NtfyResponse(success=False, error={self.error!r})"


# ---------------------------------------------------------------------------
# NtfyClient
# ---------------------------------------------------------------------------


class NtfyClient:
    """Client for publishing messages to an ntfy server.

    Wraps a single (url, topic, token) combination and exposes a `send()`
    method that never raises on network or HTTP errors — all outcomes are
    communicated through `NtfyResponse`.
    """

    def __init__(
        self,
        url: str,
        topic: str,
        token: str = "",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initializes the ntfy client.

        Args:
            url: Base URL of the ntfy server (e.g. ``"https://ntfy.sh"``).
            topic: The ntfy topic to publish to.
            token: Optional Bearer access token for authentication.
            timeout: HTTP request timeout in seconds.

        Raises:
            ValueError: If *url* or *topic* is empty.
        """
        if not url or not url.strip():
            raise ValueError("ntfy server URL must not be empty")
        if not topic or not topic.strip():
            raise ValueError("ntfy topic must not be empty")

        self._url: str = url.rstrip("/")
        self._topic: str = topic.strip()
        self._token: str = token
        self._timeout: int = timeout

    @classmethod
    def from_config(cls, config: "CobotsConfig") -> "NtfyClient":
        """Creates an `NtfyClient` from a `CobotsConfig` object.

        Reads url, topic, and token from ``config.ntfy``.

        Args:
            config: A `CobotsConfig` instance (imported from
                ``cobots_lib.workspace.config``).

        Raises:
            ValueError: If ``config.ntfy.topic`` is empty.
        """
        ntfy_cfg = config.ntfy
        return cls(
            url=ntfy_cfg.url,
            topic=ntfy_cfg.topic,
            token=ntfy_cfg.token,
        )

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def send(
        self,
        message: str,
        *,
        title: str | None = None,
        priority: int | None = None,
        tags: list[str] | None = None,
        click: str | None = None,
        markdown: bool = False,
    ) -> NtfyResponse:
        """Publishes a message to the configured ntfy topic.

        Args:
            message: The notification body text. Must be non-empty.
            title: Optional notification title.
            priority: Optional priority (1–5). ``None`` uses the server
                default (3).
            tags: Optional list of tag strings (emoji shortcodes, etc.).
            click: Optional URL to open when the notification is clicked.
            markdown: If ``True``, the message is rendered as Markdown.

        Returns:
            An `NtfyResponse` with ``success=True`` and ``message_id`` on
            success, or ``success=False`` with an ``error`` description on
            failure.

        Raises:
            ValueError: If *message* is empty or *priority* is invalid.

        Note:
            Network and HTTP errors are **never** raised — they are
            captured in the returned `NtfyResponse`.
        """
        # -- Validation (fail-fast, in the order defined by section 6.3) --

        # 1. Topic was already validated in __init__, but guard anyway.
        if not self._topic:
            raise ValueError("ntfy topic must not be empty")

        # 2. Message must be non-empty.
        if not message or not message.strip():
            raise ValueError("notification message must not be empty")

        # 3. Priority must be valid (if provided).
        if priority is not None and priority not in VALID_PRIORITIES:
            raise ValueError(
                f"invalid priority {priority!r}: must be one of "
                f"{sorted(VALID_PRIORITIES)}"
            )

        # 4. URL sanity check.
        if not (
            self._url.startswith("http://")
            or self._url.startswith("https://")
        ):
            raise ValueError(
                f"ntfy URL must start with http:// or https://, "
                f"got {self._url!r}"
            )

        # -- Build the request -------------------------------------------

        endpoint = f"{self._url}/{self._topic}"
        headers: dict[str, str] = {}

        if title:
            headers["Title"] = title

        if priority is not None:
            headers["Priority"] = str(priority)

        if tags:
            headers["Tags"] = ",".join(tags)

        if click:
            headers["Click"] = click

        if markdown:
            headers["Markdown"] = "yes"

        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        body = message.encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers=headers,
            method="POST",
        )

        # -- Execute the request -----------------------------------------

        return self._execute(req)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _execute(self, req: urllib.request.Request) -> NtfyResponse:
        """Executes *req* and translates the outcome to `NtfyResponse`.

        HTTP and network errors are caught here so that `send()` never
        raises for runtime failures.
        """
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw_body = resp.read().decode("utf-8")
                data = json.loads(raw_body)
                return NtfyResponse(
                    success=True,
                    status_code=resp.status,
                    message_id=data.get("id"),
                    raw=data,
                )
        except urllib.error.HTTPError as exc:
            # The server returned an error status code (4xx / 5xx).
            error_msg = f"HTTP {exc.code}"
            raw_data: dict | None = None
            try:
                raw_body = exc.read().decode("utf-8")
                raw_data = json.loads(raw_body)
                error_msg = raw_data.get("error", error_msg)
            except Exception:
                pass
            return NtfyResponse(
                success=False,
                status_code=exc.code,
                error=error_msg,
                raw=raw_data,
            )
        except urllib.error.URLError as exc:
            # Network-level error (DNS failure, connection refused, etc.).
            return NtfyResponse(
                success=False,
                status_code=0,
                error=f"network error: {exc.reason}",
            )
        except OSError as exc:
            # Catch-all for lower-level socket / OS errors (includes
            # timeouts on some platforms).
            return NtfyResponse(
                success=False,
                status_code=0,
                error=f"connection error: {exc}",
            )
        except Exception as exc:
            # Unexpected errors (e.g. malformed JSON from server).
            return NtfyResponse(
                success=False,
                status_code=0,
                error=f"unexpected error: {exc}",
            )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def send_notification(
    config: "CobotsConfig",
    message: str,
    *,
    title: str | None = None,
    priority: int | None = None,
    tags: list[str] | None = None,
    click: str | None = None,
    markdown: bool = False,
) -> NtfyResponse:
    """Convenience function: send a notification using the given config.

    Creates an `NtfyClient` from *config* and calls `send()`. This is the
    simplest way to fire a one-off notification from another skill:

    .. code-block:: python

        from cobots_lib.workspace.working_dir import load_config
        from cobots_lib.ntfy.client import send_notification

        config = load_config()
        result = send_notification(config, "Task done!", tags=["tada"])

    Args:
        config: A `CobotsConfig` instance.
        message: The notification body text.
        title: Optional notification title.
        priority: Optional priority (1–5).
        tags: Optional list of tag strings.
        click: Optional click URL.
        markdown: If ``True``, render message as Markdown.

    Returns:
        An `NtfyResponse` describing the outcome.

    Raises:
        ValueError: If ``config.ntfy.topic`` is empty, *message* is
            empty, or *priority* is invalid.
    """
    client = NtfyClient.from_config(config)
    return client.send(
        message,
        title=title,
        priority=priority,
        tags=tags,
        click=click,
        markdown=markdown,
    )
