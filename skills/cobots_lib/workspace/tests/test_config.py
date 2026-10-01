"""Unit tests for the cobots workspace configuration data model."""

import os
import sys
import tempfile
import unittest

_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.workspace.config import CobotsConfig


class TestCobotsConfig(unittest.TestCase):
    """Verify configuration defaults, overrides, and serialization."""

    def test_defaults(self) -> None:
        """Default construction populates every supported field."""
        config = CobotsConfig()

        self.assertEqual(
            config.task_status_values,
            ["pending", "underway", "done", "abandoned"],
        )
        self.assertEqual(config.task_id_length, 16)
        self.assertEqual(config.report_id_length, 16)
        self.assertEqual(config.knowledge_id_length, 16)
        self.assertEqual(config.workspace_name, "")

    def test_explicit_values(self) -> None:
        """Explicit values replace each default."""
        config = CobotsConfig(
            task_status_values=["open", "closed"],
            task_id_length=8,
            report_id_length=12,
            knowledge_id_length=20,
            workspace_name="example",
        )

        self.assertEqual(
            config.to_dict(),
            {
                "workspace_name": "example",
                "task_status_values": ["open", "closed"],
                "task_id_length": 8,
                "report_id_length": 12,
                "knowledge_id_length": 20,
            },
        )

    def test_empty_data_uses_defaults(self) -> None:
        """Empty dictionaries and YAML documents use defaults."""
        self.assertEqual(
            CobotsConfig.from_dict({}).to_dict(),
            CobotsConfig().to_dict(),
        )
        self.assertEqual(
            CobotsConfig.from_yaml("").to_dict(),
            CobotsConfig().to_dict(),
        )

    def test_yaml_round_trip(self) -> None:
        """YAML serialization preserves supported values."""
        original = CobotsConfig(
            task_status_values=["queued", "done"],
            task_id_length=10,
            report_id_length=14,
            knowledge_id_length=18,
            workspace_name="round-trip",
        )

        restored = CobotsConfig.from_yaml(original.to_yaml())

        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_file_round_trip(self) -> None:
        """File serialization preserves supported values."""
        original = CobotsConfig(workspace_name="file-round-trip")
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
        ) as config_file:
            path = config_file.name

        try:
            original.write_file(path)
            restored = CobotsConfig.from_file(path)
            self.assertEqual(restored.to_dict(), original.to_dict())
        finally:
            os.unlink(path)

    def test_repr_contains_class_name_and_values(self) -> None:
        """The representation identifies the class and current values."""
        representation = repr(CobotsConfig(workspace_name="example"))

        self.assertTrue(representation.startswith("CobotsConfig("))
        self.assertIn("example", representation)


if __name__ == "__main__":
    unittest.main()
