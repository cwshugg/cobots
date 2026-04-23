"""
config.py - Cobots configuration data model.

Defines the `CobotsConfig` class, which represents the contents of a
`cobots-config.yaml` file. Instances can be serialized directly to YAML
and loaded back from YAML.
"""

import yaml

from cobots_lib.workspace.constants import CONFIG_FILE_NAME


class NtfyConfig:
    """Configuration for the ntfy notification integration.

    Holds the server URL, topic, optional authentication token,
    notification mode, and optional custom confidential messages
    used by the ntfy notification skill. Instances can be converted
    to and from plain dictionaries for YAML serialization.
    """

    # Default ntfy server URL (the public ntfy.sh instance).
    DEFAULT_URL = "https://ntfy.sh"

    # Default notification mode. Controls what messages can be sent.
    # Valid values: "open", "confidential", "closed".
    DEFAULT_MODE = "confidential"

    # The set of valid mode strings.
    VALID_MODES = {"open", "confidential", "closed"}

    def __init__(
        self,
        url: str | None = None,
        topic: str | None = None,
        token: str | None = None,
        mode: str | None = None,
        confidential_messages: list[dict] | None = None,
        confidential_titles: list[dict] | None = None,
    ) -> None:
        """Initializes the ntfy configuration with the given or
        default values.

        Args:
            url: Base URL of the ntfy server.
            topic: The ntfy topic to publish to.
            token: Optional Bearer access token for authentication.
            mode: Notification mode ("open", "confidential", or
                "closed"). Defaults to "confidential".
            confidential_messages: Optional list of dicts with "key"
                and "message" fields to override/extend the hardcoded
                default confidential messages. ``None`` means use the
                hardcoded defaults.
            confidential_titles: Optional list of dicts with "key"
                and "title" fields to override/extend the hardcoded
                default confidential titles. ``None`` means use the
                hardcoded defaults.

        Raises:
            ValueError: If *mode* is not a valid mode string.

        Note: URL validation (scheme check) is deferred to
        `NtfyClient.send()` so that config objects can be
        constructed and serialized without network constraints.
        """
        self.url: str = (url or self.DEFAULT_URL).rstrip("/")
        self.topic: str = topic or ""
        self.token: str = token or ""

        resolved_mode = mode or self.DEFAULT_MODE
        if resolved_mode not in self.VALID_MODES:
            raise ValueError(
                f"invalid ntfy mode {resolved_mode!r}: "
                f"must be one of {sorted(self.VALID_MODES)}"
            )
        self.mode: str = resolved_mode
        self.confidential_messages: list[dict] | None = (
            confidential_messages
        )
        self.confidential_titles: list[dict] | None = (
            confidential_titles
        )

    def to_dict(self) -> dict:
        """Returns the ntfy configuration as a plain dictionary.

        The ``confidential_messages`` and ``confidential_titles``
        keys are only included when a custom list has been explicitly
        set (i.e. not ``None``).
        """
        result: dict = {
            "url": self.url,
            "topic": self.topic,
            "token": self.token,
            "mode": self.mode,
        }
        if self.confidential_messages is not None:
            result["confidential_messages"] = self.confidential_messages
        if self.confidential_titles is not None:
            result["confidential_titles"] = self.confidential_titles
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "NtfyConfig":
        """Creates an `NtfyConfig` from a plain dictionary."""
        return cls(
            url=data.get("url"),
            topic=data.get("topic"),
            token=data.get("token"),
            mode=data.get("mode"),
            confidential_messages=data.get("confidential_messages"),
            confidential_titles=data.get("confidential_titles"),
        )

    def __repr__(self) -> str:
        safe = self.to_dict()
        if safe.get("token"):
            safe["token"] = "***"
        return f"NtfyConfig({safe!r})"


class StatusConfig:
    """Configuration for the cobots status skill.

    Holds refresh rate and activity count settings.
    Follows the same *structure* as ``NtfyConfig`` but uses defensive
    clamping instead of raising on invalid input — the status skill should
    never crash on bad configuration data.
    """

    DEFAULT_REFRESH_RATE: int = 5       # seconds (matches requirements)
    DEFAULT_ACTIVITY_COUNT: int = 20
    MIN_REFRESH_RATE: int = 2
    MAX_REFRESH_RATE: int = 3600
    MIN_ACTIVITY_COUNT: int = 1
    MAX_ACTIVITY_COUNT: int = 100

    def __init__(
        self,
        refresh_rate: int | None = None,
        activity_count: int | None = None,
    ) -> None:
        raw_rate = refresh_rate if refresh_rate is not None else self.DEFAULT_REFRESH_RATE
        try:
            raw_rate_int = int(raw_rate)
        except (ValueError, TypeError):
            raw_rate_int = self.DEFAULT_REFRESH_RATE
        self.refresh_rate: int = max(
            self.MIN_REFRESH_RATE, min(raw_rate_int, self.MAX_REFRESH_RATE)
        )

        raw_count = activity_count if activity_count is not None else self.DEFAULT_ACTIVITY_COUNT
        try:
            raw_count_int = int(raw_count)
        except (ValueError, TypeError):
            raw_count_int = self.DEFAULT_ACTIVITY_COUNT
        self.activity_count: int = max(
            self.MIN_ACTIVITY_COUNT, min(raw_count_int, self.MAX_ACTIVITY_COUNT)
        )

    def to_dict(self) -> dict:
        """Returns the status configuration as a plain dictionary."""
        return {
            "refresh_rate": self.refresh_rate,
            "activity_count": self.activity_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StatusConfig":
        """Creates a ``StatusConfig`` from a plain dictionary."""
        return cls(
            refresh_rate=data.get("refresh_rate"),
            activity_count=data.get("activity_count"),
        )

    def __repr__(self) -> str:
        return f"StatusConfig({self.to_dict()!r})"


class CobotsConfig:
    """Represents the cobots configuration.

    Fields will be added over time as the config schema evolves. Instances
    can be converted to and from YAML via `to_yaml` / `from_yaml`.
    """

    # Default task status values used when no config file overrides them.
    DEFAULT_TASK_STATUS_VALUES = ["pending", "underway", "done", "abandoned"]

    # Default length (in hex characters) for randomly generated task IDs.
    DEFAULT_TASK_ID_LENGTH = 16

    # Default length (in hex characters) for randomly generated report IDs.
    DEFAULT_REPORT_ID_LENGTH = 16

    def __init__(
        self,
        task_status_values: list[str] | None = None,
        task_id_length: int | None = None,
        report_id_length: int | None = None,
        ntfy: "NtfyConfig | None" = None,
        workspace_name: str = "",
        status: "StatusConfig | None" = None,
    ) -> None:
        """Initializes the configuration with the given or default values."""
        self.task_status_values = (
            task_status_values
            if task_status_values is not None
            else list(self.DEFAULT_TASK_STATUS_VALUES)
        )
        self.task_id_length = (
            task_id_length
            if task_id_length is not None
            else self.DEFAULT_TASK_ID_LENGTH
        )
        self.report_id_length = (
            report_id_length
            if report_id_length is not None
            else self.DEFAULT_REPORT_ID_LENGTH
        )
        self.ntfy = ntfy if ntfy is not None else NtfyConfig()
        self.workspace_name: str = workspace_name
        self.status = status if status is not None else StatusConfig()

    def to_dict(self) -> dict:
        """Returns the configuration as a plain dictionary."""
        return {
            "workspace_name": self.workspace_name,
            "task_status_values": self.task_status_values,
            "task_id_length": self.task_id_length,
            "report_id_length": self.report_id_length,
            "ntfy": self.ntfy.to_dict(),
            "status": self.status.to_dict(),
        }

    def to_yaml(self) -> str:
        """Serializes the configuration to a YAML string."""
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CobotsConfig":
        """Creates a `CobotsConfig` from a plain dictionary."""
        config = cls(
            task_status_values=data.get("task_status_values"),
            task_id_length=data.get("task_id_length"),
            report_id_length=data.get("report_id_length"),
            ntfy=NtfyConfig.from_dict(data.get("ntfy", {})),
            workspace_name=data.get("workspace_name", ""),
            status=StatusConfig.from_dict(data.get("status", {})),
        )
        return config

    @classmethod
    def from_yaml(cls, text: str) -> "CobotsConfig":
        """Deserializes a `CobotsConfig` from a YAML string."""
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, path: str) -> "CobotsConfig":
        """Loads a `CobotsConfig` from a YAML file on disk."""
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_yaml(fh.read())

    def write_file(self, path: str) -> None:
        """Writes the configuration to a YAML file on disk."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_yaml())

    def __repr__(self) -> str:
        safe = self.to_dict()
        if safe.get("ntfy", {}).get("token"):
            safe["ntfy"]["token"] = "***"
        return f"CobotsConfig({safe!r})"
