"""
client.py - ntfy notification client for the Cobots Collective.

Implements the `NtfyClient` class and `send_notification()` convenience
function for publishing messages to an ntfy.sh server. Uses only the
Python standard library (`urllib.request`) — no third-party HTTP
dependencies.

Supports three notification modes:

- **open** — any message content and title text is allowed.
- **confidential** — only predefined messages and titles (selected by
  key) are allowed. This prevents leaking sensitive project data.
- **closed** — all sends are refused.
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

# The set of valid notification mode strings.
VALID_MODES = {"open", "confidential", "closed"}

# The default notification mode when none is specified.
DEFAULT_MODE = "confidential"


# ---------------------------------------------------------------------------
# Default confidential messages
# ---------------------------------------------------------------------------

# Hardcoded predefined messages for confidential mode. Each entry maps
# a snake_case key to a human-readable display string. When in
# ``confidential`` mode, only these keys (or custom overrides from
# config) are accepted by `NtfyClient.send()`.
DEFAULT_CONFIDENTIAL_MESSAGES: dict[str, str] = {
    "task_started": "A task has been started",
    "task_done": "A task has been completed",
    "task_blocked": "A task is blocked",
    "build_started": "Build started",
    "build_done": "Build completed",
    "build_failed": "Build failed",
    "tests_passed": "All tests passed",
    "tests_failed": "Tests failed",
    "review_requested": "Code review requested",
    "review_done": "Code review completed",
    "question_for_human": "A cobot has a question for you",
    "deploy_started": "Deployment started",
    "deploy_done": "Deployment completed",
    "deploy_failed": "Deployment failed",
    "error_occurred": "An error occurred",
    "waiting_for_input": "Waiting for human input",
    "report_ready": "A report is ready for review",
    "pipeline_started": "Pipeline started",
    "pipeline_done": "Pipeline completed",
}


# ---------------------------------------------------------------------------
# Default confidential titles
# ---------------------------------------------------------------------------

# Hardcoded predefined titles for confidential mode. Each entry maps
# a snake_case key to a human-readable display string. When in
# ``confidential`` mode, only these keys (or custom overrides from
# config) are accepted as the ``title`` parameter by
# `NtfyClient.send()`.
DEFAULT_CONFIDENTIAL_TITLES: dict[str, str] = {
    "task_update": "Task Update",
    "build_update": "Build Update",
    "test_update": "Test Update",
    "review_update": "Review Update",
    "deploy_update": "Deployment Update",
    "pipeline_update": "Pipeline Update",
    "error_alert": "Error Alert",
    "question": "Question",
    "report": "Report",
    "general": "Notification",
}


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

    The client operates in one of three modes:

    - **open** — any message content and title text is accepted.
    - **confidential** — only predefined message keys and title keys
      are accepted. Keys are resolved to their display strings before
      sending.
    - **closed** — all sends are immediately refused.
    """

    def __init__(
        self,
        url: str,
        topic: str,
        token: str = "",
        timeout: int = DEFAULT_TIMEOUT,
        mode: str = DEFAULT_MODE,
        confidential_messages: dict[str, str] | None = None,
        confidential_titles: dict[str, str] | None = None,
    ) -> None:
        """Initializes the ntfy client.

        Args:
            url: Base URL of the ntfy server (e.g. ``"https://ntfy.sh"``).
            topic: The ntfy topic to publish to.
            token: Optional Bearer access token for authentication.
            timeout: HTTP request timeout in seconds.
            mode: Notification mode — ``"open"``, ``"confidential"``,
                or ``"closed"``. Defaults to ``"confidential"``.
            confidential_messages: Optional dict mapping message keys
                to display strings. If ``None``, the hardcoded
                `DEFAULT_CONFIDENTIAL_MESSAGES` are used.
            confidential_titles: Optional dict mapping title keys
                to display strings. If ``None``, the hardcoded
                `DEFAULT_CONFIDENTIAL_TITLES` are used.

        Raises:
            ValueError: If *url* or *topic* is empty, or *mode* is
                not a valid mode string.
        """
        if not url or not url.strip():
            raise ValueError("ntfy server URL must not be empty")
        if not topic or not topic.strip():
            raise ValueError("ntfy topic must not be empty")
        if mode not in VALID_MODES:
            raise ValueError(
                f"invalid ntfy mode {mode!r}: "
                f"must be one of {sorted(VALID_MODES)}"
            )

        self._url: str = url.rstrip("/")
        self._topic: str = topic.strip()
        self._token: str = token
        self._timeout: int = timeout
        self._mode: str = mode
        self._confidential_messages: dict[str, str] = (
            confidential_messages
            if confidential_messages is not None
            else dict(DEFAULT_CONFIDENTIAL_MESSAGES)
        )
        self._confidential_titles: dict[str, str] = (
            confidential_titles
            if confidential_titles is not None
            else dict(DEFAULT_CONFIDENTIAL_TITLES)
        )

    @classmethod
    def from_config(cls, config: "CobotsConfig") -> "NtfyClient":
        """Creates an `NtfyClient` from a `CobotsConfig` object.

        Reads url, topic, token, mode, confidential_messages, and
        confidential_titles from ``config.ntfy``.

        Args:
            config: A `CobotsConfig` instance (imported from
                ``cobots_lib.workspace.config``).

        Raises:
            ValueError: If ``config.ntfy.topic`` is empty or
                ``config.ntfy.mode`` is invalid.
        """
        ntfy_cfg = config.ntfy

        # Convert config's list-of-dicts to a key→message dict, or
        # None to use the hardcoded defaults.
        conf_msgs: dict[str, str] | None = None
        if ntfy_cfg.confidential_messages is not None:
            conf_msgs = {
                entry["key"]: entry["message"]
                for entry in ntfy_cfg.confidential_messages
            }

        # Convert config's list-of-dicts to a key→title dict, or
        # None to use the hardcoded defaults.
        conf_titles: dict[str, str] | None = None
        if ntfy_cfg.confidential_titles is not None:
            conf_titles = {
                entry["key"]: entry["title"]
                for entry in ntfy_cfg.confidential_titles
            }

        return cls(
            url=ntfy_cfg.url,
            topic=ntfy_cfg.topic,
            token=ntfy_cfg.token,
            mode=ntfy_cfg.mode,
            confidential_messages=conf_msgs,
            confidential_titles=conf_titles,
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

        Behavior depends on the client's mode:

        - **open** — *message* and *title* are sent as-is.
        - **confidential** — *message* must be a valid predefined key.
          The key is looked up and the corresponding display string is
          sent instead. If *title* is provided, it must also be a
          valid predefined title key — it is resolved to the
          corresponding display string. If *title* is ``None``, no
          title is sent.
        - **closed** — returns an ``NtfyResponse`` with
          ``success=False`` immediately.

        Args:
            message: The notification body text (open mode) or a
                predefined message key (confidential mode). Must be
                non-empty.
            title: Optional notification title (open mode) or a
                predefined title key (confidential mode).
            priority: Optional priority (1–5). ``None`` uses the server
                default (3).
            tags: Optional list of tag strings (emoji shortcodes, etc.).
            click: Optional URL to open when the notification is clicked.
            markdown: If ``True``, the message is rendered as Markdown.

        Returns:
            An `NtfyResponse` with ``success=True`` and ``message_id``
            on success, or ``success=False`` with an ``error``
            description on failure.

        Raises:
            ValueError: If *message* is empty, *priority* is invalid,
                or (in confidential mode) *message* is not a valid
                message key or *title* is not a valid title key.

        Note:
            Network and HTTP errors are **never** raised — they are
            captured in the returned `NtfyResponse`.
        """
        # -- Mode check (fail-fast) -----------------------------------------

        # Closed mode: refuse immediately.
        if self._mode == "closed":
            return NtfyResponse(
                success=False,
                status_code=0,
                error="notifications are disabled (mode=closed)",
            )

        # -- Validation (fail-fast, in the order defined by section 6.3) --

        # 1. Topic was already validated in __init__, but guard anyway.
        if not self._topic:
            raise ValueError("ntfy topic must not be empty")

        # 2. Message must be non-empty.
        if not message or not message.strip():
            raise ValueError("notification message must not be empty")

        # 3. Confidential mode: resolve message key to display string.
        if self._mode == "confidential":
            if message not in self._confidential_messages:
                valid_keys = sorted(self._confidential_messages.keys())
                raise ValueError(
                    f"unknown message key {message!r} "
                    f"(mode=confidential). "
                    f"Valid keys: {', '.join(valid_keys)}"
                )
            message = self._confidential_messages[message]

            # 3b. Validate title key (if provided) against allowed
            # title keys and resolve to display string.
            if title is not None:
                if title not in self._confidential_titles:
                    valid_title_keys = sorted(
                        self._confidential_titles.keys()
                    )
                    raise ValueError(
                        f"unknown title key {title!r} "
                        f"(mode=confidential). "
                        f"Valid keys: "
                        f"{', '.join(valid_title_keys)}"
                    )
                title = self._confidential_titles[title]

        # 4. Priority must be valid (if provided).
        if priority is not None and priority not in VALID_PRIORITIES:
            raise ValueError(
                f"invalid priority {priority!r}: must be one of "
                f"{sorted(VALID_PRIORITIES)}"
            )

        # 5. URL sanity check.
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
