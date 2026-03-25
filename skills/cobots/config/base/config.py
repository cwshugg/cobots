"""
config.py - Cobots configuration data model.

Defines the `CobotsConfig` class, which represents the contents of a
`cobots-config.yaml` file. Instances can be serialized directly to YAML
and loaded back from YAML.
"""

import yaml

from config.base.constants import CONFIG_FILE_NAME


class CobotsConfig:
    """Represents the cobots configuration.

    Fields will be added over time as the config schema evolves. Instances
    can be converted to and from YAML via `to_yaml` / `from_yaml`.
    """

    # Default task status values used when no config file overrides them.
    DEFAULT_TASK_STATUS_VALUES = ["untouched", "underway", "blocked", "done"]

    def __init__(
        self,
        task_status_values: list[str] | None = None,
    ) -> None:
        """Initializes the configuration with the given or default values."""
        self.task_status_values = (
            task_status_values
            if task_status_values is not None
            else list(self.DEFAULT_TASK_STATUS_VALUES)
        )

    def to_dict(self) -> dict:
        """Returns the configuration as a plain dictionary."""
        return {
            "task_status_values": self.task_status_values,
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
        return f"CobotsConfig({self.to_dict()!r})"
