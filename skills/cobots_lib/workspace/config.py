"""Cobots workspace configuration data model."""

import yaml


class CobotsConfig:
    """Represent the contents of a cobots workspace configuration file."""

    DEFAULT_TASK_STATUS_VALUES = ["pending", "underway", "done", "abandoned"]
    DEFAULT_TASK_ID_LENGTH = 16
    DEFAULT_REPORT_ID_LENGTH = 16
    DEFAULT_KNOWLEDGE_ID_LENGTH = 16

    def __init__(
        self,
        task_status_values: list[str] | None = None,
        task_id_length: int | None = None,
        report_id_length: int | None = None,
        knowledge_id_length: int | None = None,
        workspace_name: str = "",
    ) -> None:
        """Initialize configuration fields with explicit or default values."""
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
        self.knowledge_id_length = (
            knowledge_id_length
            if knowledge_id_length is not None
            else self.DEFAULT_KNOWLEDGE_ID_LENGTH
        )
        self.workspace_name = workspace_name

    def to_dict(self) -> dict:
        """Return the configuration as a plain dictionary."""
        return {
            "workspace_name": self.workspace_name,
            "task_status_values": self.task_status_values,
            "task_id_length": self.task_id_length,
            "report_id_length": self.report_id_length,
            "knowledge_id_length": self.knowledge_id_length,
        }

    def to_yaml(self) -> str:
        """Serialize the configuration to YAML."""
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CobotsConfig":
        """Create configuration from a plain dictionary."""
        return cls(
            task_status_values=data.get("task_status_values"),
            task_id_length=data.get("task_id_length"),
            report_id_length=data.get("report_id_length"),
            knowledge_id_length=data.get("knowledge_id_length"),
            workspace_name=data.get("workspace_name", ""),
        )

    @classmethod
    def from_yaml(cls, text: str) -> "CobotsConfig":
        """Deserialize configuration from YAML."""
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, path: str) -> "CobotsConfig":
        """Load configuration from a YAML file."""
        with open(path, "r", encoding="utf-8") as config_file:
            return cls.from_yaml(config_file.read())

    def write_file(self, path: str) -> None:
        """Write configuration to a YAML file."""
        with open(path, "w", encoding="utf-8") as config_file:
            config_file.write(self.to_yaml())

    def __repr__(self) -> str:
        """Return a readable representation of the configuration."""
        return f"CobotsConfig({self.to_dict()!r})"
