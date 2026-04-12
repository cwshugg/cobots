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

    Holds the server URL, topic, and optional authentication token
    used by the ntfy notification skill. Instances can be converted
    to and from plain dictionaries for YAML serialization.
    """

    # Default ntfy server URL (the public ntfy.sh instance).
    DEFAULT_URL = "https://ntfy.sh"

    def __init__(
        self,
        url: str | None = None,
        topic: str | None = None,
        token: str | None = None,
    ) -> None:
        """Initializes the ntfy configuration with the given or
        default values.

        Note: URL validation (scheme check) is deferred to
        `NtfyClient.send()` so that config objects can be
        constructed and serialized without network constraints.
        """
        self.url: str = (url or self.DEFAULT_URL).rstrip("/")
        self.topic: str = topic or ""
        self.token: str = token or ""

    def to_dict(self) -> dict:
        """Returns the ntfy configuration as a plain dictionary."""
        return {
            "url": self.url,
            "topic": self.topic,
            "token": self.token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NtfyConfig":
        """Creates an `NtfyConfig` from a plain dictionary."""
        return cls(
            url=data.get("url"),
            topic=data.get("topic"),
            token=data.get("token"),
        )

    def __repr__(self) -> str:
        safe = self.to_dict()
        if safe.get("token"):
            safe["token"] = "***"
        return f"NtfyConfig({safe!r})"


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

    def to_dict(self) -> dict:
        """Returns the configuration as a plain dictionary."""
        return {
            "workspace_name": self.workspace_name,
            "task_status_values": self.task_status_values,
            "task_id_length": self.task_id_length,
            "report_id_length": self.report_id_length,
            "ntfy": self.ntfy.to_dict(),
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
