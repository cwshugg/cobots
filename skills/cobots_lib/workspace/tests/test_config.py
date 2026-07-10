"""
test_config.py - Unit tests for the cobots configuration data model.

Tests both `NtfyConfig` and `CobotsConfig`, including serialization
round-trips, default values, backward compatibility with config
files that predate the ntfy section, and the `workspace_name` field.
"""

import os
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: ensure cobots_lib is importable regardless of working directory.
# ---------------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from cobots_lib.workspace.config import CobotsConfig, NtfyConfig


# ===================================================================
# NtfyConfig tests
# ===================================================================


class TestNtfyConfigDefaults(unittest.TestCase):
    """Verify that `NtfyConfig()` with no arguments produces the
    expected default values.
    """

    def test_default_url(self) -> None:
        cfg = NtfyConfig()
        self.assertEqual(cfg.url, "https://ntfy.sh")

    def test_default_topic_is_empty(self) -> None:
        cfg = NtfyConfig()
        self.assertEqual(cfg.topic, "")

    def test_default_token_is_empty(self) -> None:
        cfg = NtfyConfig()
        self.assertEqual(cfg.token, "")


class TestNtfyConfigInit(unittest.TestCase):
    """Verify explicit field assignment through `__init__`."""

    def test_custom_url(self) -> None:
        cfg = NtfyConfig(url="https://my-ntfy.example.com")
        self.assertEqual(cfg.url, "https://my-ntfy.example.com")

    def test_trailing_slash_stripped_from_url(self) -> None:
        cfg = NtfyConfig(url="https://ntfy.sh/")
        self.assertEqual(cfg.url, "https://ntfy.sh")

    def test_multiple_trailing_slashes_stripped(self) -> None:
        cfg = NtfyConfig(url="https://ntfy.sh///")
        self.assertEqual(cfg.url, "https://ntfy.sh")

    def test_custom_topic(self) -> None:
        cfg = NtfyConfig(topic="my-cobots-topic")
        self.assertEqual(cfg.topic, "my-cobots-topic")

    def test_custom_token(self) -> None:
        cfg = NtfyConfig(token="tk_abc123")
        self.assertEqual(cfg.token, "tk_abc123")

    def test_none_url_falls_back_to_default(self) -> None:
        cfg = NtfyConfig(url=None)
        self.assertEqual(cfg.url, NtfyConfig.DEFAULT_URL)

    def test_empty_string_url_falls_back_to_default(self) -> None:
        cfg = NtfyConfig(url="")
        self.assertEqual(cfg.url, NtfyConfig.DEFAULT_URL)

    def test_none_topic_becomes_empty_string(self) -> None:
        cfg = NtfyConfig(topic=None)
        self.assertEqual(cfg.topic, "")

    def test_none_token_becomes_empty_string(self) -> None:
        cfg = NtfyConfig(token=None)
        self.assertEqual(cfg.token, "")


class TestNtfyConfigToDict(unittest.TestCase):
    """Verify dictionary serialization."""

    def test_default_to_dict(self) -> None:
        d = NtfyConfig().to_dict()
        self.assertEqual(d, {
            "url": "https://ntfy.sh",
            "topic": "",
            "token": "",
            "mode": "confidential",
        })

    def test_custom_to_dict(self) -> None:
        cfg = NtfyConfig(
            url="https://custom.example.com/",
            topic="my-topic",
            token="tk_xyz",
        )
        d = cfg.to_dict()
        self.assertEqual(d["url"], "https://custom.example.com")
        self.assertEqual(d["topic"], "my-topic")
        self.assertEqual(d["token"], "tk_xyz")


class TestNtfyConfigFromDict(unittest.TestCase):
    """Verify construction from a dictionary."""

    def test_full_dict(self) -> None:
        data = {
            "url": "https://custom.example.com",
            "topic": "my-topic",
            "token": "tk_xyz",
        }
        cfg = NtfyConfig.from_dict(data)
        self.assertEqual(cfg.url, "https://custom.example.com")
        self.assertEqual(cfg.topic, "my-topic")
        self.assertEqual(cfg.token, "tk_xyz")

    def test_empty_dict_produces_defaults(self) -> None:
        cfg = NtfyConfig.from_dict({})
        self.assertEqual(cfg.url, NtfyConfig.DEFAULT_URL)
        self.assertEqual(cfg.topic, "")
        self.assertEqual(cfg.token, "")

    def test_partial_dict_fills_defaults(self) -> None:
        cfg = NtfyConfig.from_dict({"topic": "partial"})
        self.assertEqual(cfg.url, NtfyConfig.DEFAULT_URL)
        self.assertEqual(cfg.topic, "partial")
        self.assertEqual(cfg.token, "")


class TestNtfyConfigRoundTrip(unittest.TestCase):
    """Verify `to_dict` -> `from_dict` round-trip preserves values."""

    def test_round_trip_defaults(self) -> None:
        original = NtfyConfig()
        restored = NtfyConfig.from_dict(original.to_dict())
        self.assertEqual(original.to_dict(), restored.to_dict())

    def test_round_trip_custom(self) -> None:
        original = NtfyConfig(
            url="https://self-hosted.example.com/",
            topic="cobots-alerts",
            token="tk_secret",
        )
        restored = NtfyConfig.from_dict(original.to_dict())
        self.assertEqual(original.to_dict(), restored.to_dict())


class TestNtfyConfigRepr(unittest.TestCase):
    """Verify `__repr__` produces a readable string with masked token."""

    def test_repr_contains_class_name(self) -> None:
        cfg = NtfyConfig()
        self.assertTrue(repr(cfg).startswith("NtfyConfig("))

    def test_repr_masks_nonempty_token(self) -> None:
        """A non-empty token must be replaced with '***' in repr."""
        cfg = NtfyConfig(token="tk_secret_value")
        r = repr(cfg)
        self.assertNotIn("tk_secret_value", r)
        self.assertIn("***", r)

    def test_repr_empty_token_not_masked(self) -> None:
        """An empty token should appear as-is (no '***')."""
        cfg = NtfyConfig(token="")
        r = repr(cfg)
        self.assertNotIn("***", r)


# ===================================================================
# CobotsConfig tests (ntfy integration)
# ===================================================================


class TestCobotsConfigNtfyDefaults(unittest.TestCase):
    """Verify that `CobotsConfig()` with no arguments includes a
    default `NtfyConfig`.
    """

    def test_ntfy_attribute_exists(self) -> None:
        cfg = CobotsConfig()
        self.assertIsInstance(cfg.ntfy, NtfyConfig)

    def test_ntfy_default_url(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.ntfy.url, NtfyConfig.DEFAULT_URL)

    def test_ntfy_default_topic(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.ntfy.topic, "")

    def test_ntfy_default_token(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.ntfy.token, "")


class TestCobotsConfigNtfyExplicit(unittest.TestCase):
    """Verify passing an explicit `NtfyConfig` to `CobotsConfig`."""

    def test_custom_ntfy_is_stored(self) -> None:
        ntfy = NtfyConfig(
            url="https://custom.example.com",
            topic="my-topic",
            token="tk_123",
        )
        cfg = CobotsConfig(ntfy=ntfy)
        self.assertIs(cfg.ntfy, ntfy)
        self.assertEqual(cfg.ntfy.topic, "my-topic")


class TestCobotsConfigToDict(unittest.TestCase):
    """Verify `to_dict` includes the ntfy section."""

    def test_ntfy_key_present(self) -> None:
        d = CobotsConfig().to_dict()
        self.assertIn("ntfy", d)

    def test_ntfy_dict_structure(self) -> None:
        d = CobotsConfig().to_dict()
        self.assertEqual(d["ntfy"], {
            "url": "https://ntfy.sh",
            "topic": "",
            "token": "",
            "mode": "confidential",
        })

    def test_custom_ntfy_in_dict(self) -> None:
        ntfy = NtfyConfig(topic="alerts", token="tk_abc")
        cfg = CobotsConfig(ntfy=ntfy)
        d = cfg.to_dict()
        self.assertEqual(d["ntfy"]["topic"], "alerts")
        self.assertEqual(d["ntfy"]["token"], "tk_abc")


class TestCobotsConfigFromDict(unittest.TestCase):
    """Verify `from_dict` correctly parses the ntfy section."""

    def test_ntfy_parsed_from_dict(self) -> None:
        data = {
            "task_status_values": ["pending", "done"],
            "task_id_length": 8,
            "report_id_length": 8,
            "ntfy": {
                "url": "https://my-server.example.com",
                "topic": "cobots",
                "token": "tk_xyz",
            },
        }
        cfg = CobotsConfig.from_dict(data)
        self.assertEqual(cfg.ntfy.url, "https://my-server.example.com")
        self.assertEqual(cfg.ntfy.topic, "cobots")
        self.assertEqual(cfg.ntfy.token, "tk_xyz")


class TestCobotsConfigBackwardCompatibility(unittest.TestCase):
    """Verify that config data without an ntfy section loads without
    error, with sensible defaults applied.
    """

    def test_missing_ntfy_section_uses_defaults(self) -> None:
        """Simulates a pre-ntfy config file."""
        data = {
            "task_status_values": ["pending", "underway", "done"],
            "task_id_length": 16,
            "report_id_length": 16,
        }
        cfg = CobotsConfig.from_dict(data)
        self.assertIsInstance(cfg.ntfy, NtfyConfig)
        self.assertEqual(cfg.ntfy.url, NtfyConfig.DEFAULT_URL)
        self.assertEqual(cfg.ntfy.topic, "")
        self.assertEqual(cfg.ntfy.token, "")

    def test_empty_dict_loads_all_defaults(self) -> None:
        cfg = CobotsConfig.from_dict({})
        self.assertIsInstance(cfg.ntfy, NtfyConfig)
        self.assertEqual(cfg.ntfy.url, NtfyConfig.DEFAULT_URL)

    def test_empty_yaml_loads_all_defaults(self) -> None:
        cfg = CobotsConfig.from_yaml("")
        self.assertIsInstance(cfg.ntfy, NtfyConfig)
        self.assertEqual(cfg.ntfy.url, NtfyConfig.DEFAULT_URL)


class TestCobotsConfigYamlRoundTrip(unittest.TestCase):
    """Verify YAML serialization round-trips preserve ntfy values."""

    def test_round_trip_with_defaults(self) -> None:
        original = CobotsConfig()
        yaml_text = original.to_yaml()
        restored = CobotsConfig.from_yaml(yaml_text)
        self.assertEqual(
            original.to_dict(),
            restored.to_dict(),
        )

    def test_round_trip_with_custom_ntfy(self) -> None:
        ntfy = NtfyConfig(
            url="https://my-ntfy.example.com",
            topic="cobots-alerts",
            token="tk_secret_token",
        )
        original = CobotsConfig(ntfy=ntfy)
        yaml_text = original.to_yaml()
        restored = CobotsConfig.from_yaml(yaml_text)
        self.assertEqual(
            original.to_dict(),
            restored.to_dict(),
        )


class TestCobotsConfigFileRoundTrip(unittest.TestCase):
    """Verify file-based serialization round-trips preserve ntfy
    values.
    """

    def test_write_and_read_file(self) -> None:
        ntfy = NtfyConfig(
            url="https://custom.example.com",
            topic="file-test",
            token="tk_file",
        )
        original = CobotsConfig(ntfy=ntfy)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as fh:
            tmp_path = fh.name

        try:
            original.write_file(tmp_path)
            restored = CobotsConfig.from_file(tmp_path)
            self.assertEqual(
                original.to_dict(),
                restored.to_dict(),
            )
        finally:
            os.unlink(tmp_path)

    def test_read_legacy_file_without_ntfy(self) -> None:
        """Write a config file that predates ntfy, then load it."""
        legacy_yaml = (
            "task_status_values:\n"
            "- pending\n"
            "- underway\n"
            "- done\n"
            "- abandoned\n"
            "task_id_length: 16\n"
            "report_id_length: 16\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as fh:
            fh.write(legacy_yaml)
            tmp_path = fh.name

        try:
            cfg = CobotsConfig.from_file(tmp_path)
            self.assertIsInstance(cfg.ntfy, NtfyConfig)
            self.assertEqual(cfg.ntfy.url, NtfyConfig.DEFAULT_URL)
            self.assertEqual(cfg.ntfy.topic, "")
            self.assertEqual(cfg.ntfy.token, "")
            # Existing fields should still be intact.
            self.assertEqual(
                cfg.task_status_values,
                ["pending", "underway", "done", "abandoned"],
            )
        finally:
            os.unlink(tmp_path)


class TestCobotsConfigExistingFieldsUnchanged(unittest.TestCase):
    """Verify that adding ntfy did not break the existing fields."""

    def test_default_task_status_values(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(
            cfg.task_status_values,
            CobotsConfig.DEFAULT_TASK_STATUS_VALUES,
        )

    def test_default_task_id_length(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.task_id_length, 16)

    def test_default_report_id_length(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.report_id_length, 16)

    def test_custom_values_preserved(self) -> None:
        cfg = CobotsConfig(
            task_status_values=["open", "closed"],
            task_id_length=8,
            report_id_length=32,
        )
        self.assertEqual(cfg.task_status_values, ["open", "closed"])
        self.assertEqual(cfg.task_id_length, 8)
        self.assertEqual(cfg.report_id_length, 32)


# ===================================================================
# CobotsConfig tests (workspace_name)
# ===================================================================


class TestCobotsConfigWorkspaceNameDefaults(unittest.TestCase):
    """Verify that `CobotsConfig()` with no arguments defaults
    `workspace_name` to an empty string.
    """

    def test_default_workspace_name_is_empty(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(cfg.workspace_name, "")

    def test_default_workspace_name_type(self) -> None:
        cfg = CobotsConfig()
        self.assertIsInstance(cfg.workspace_name, str)


class TestCobotsConfigWorkspaceNameExplicit(unittest.TestCase):
    """Verify passing an explicit `workspace_name` to `CobotsConfig`."""

    def test_custom_workspace_name(self) -> None:
        cfg = CobotsConfig(workspace_name="my-project")
        self.assertEqual(cfg.workspace_name, "my-project")

    def test_empty_string_workspace_name(self) -> None:
        cfg = CobotsConfig(workspace_name="")
        self.assertEqual(cfg.workspace_name, "")


class TestCobotsConfigWorkspaceNameToDict(unittest.TestCase):
    """Verify `to_dict` includes `workspace_name`."""

    def test_workspace_name_key_present(self) -> None:
        d = CobotsConfig().to_dict()
        self.assertIn("workspace_name", d)

    def test_default_workspace_name_in_dict(self) -> None:
        d = CobotsConfig().to_dict()
        self.assertEqual(d["workspace_name"], "")

    def test_custom_workspace_name_in_dict(self) -> None:
        cfg = CobotsConfig(workspace_name="cobots-dev")
        d = cfg.to_dict()
        self.assertEqual(d["workspace_name"], "cobots-dev")


class TestCobotsConfigWorkspaceNameFromDict(unittest.TestCase):
    """Verify `from_dict` correctly parses `workspace_name`."""

    def test_workspace_name_parsed_from_dict(self) -> None:
        data = {
            "workspace_name": "alpha-project",
            "task_status_values": ["pending", "done"],
            "task_id_length": 8,
            "report_id_length": 8,
        }
        cfg = CobotsConfig.from_dict(data)
        self.assertEqual(cfg.workspace_name, "alpha-project")

    def test_missing_workspace_name_defaults_to_empty(self) -> None:
        data = {
            "task_status_values": ["pending", "done"],
            "task_id_length": 8,
            "report_id_length": 8,
        }
        cfg = CobotsConfig.from_dict(data)
        self.assertEqual(cfg.workspace_name, "")


class TestCobotsConfigWorkspaceNameBackwardCompatibility(unittest.TestCase):
    """Verify that config data without `workspace_name` loads without
    error, with an empty string default.
    """

    def test_legacy_config_without_workspace_name(self) -> None:
        """Simulates a config file that predates workspace_name."""
        data = {
            "task_status_values": ["pending", "underway", "done"],
            "task_id_length": 16,
            "report_id_length": 16,
            "ntfy": {
                "url": "https://ntfy.sh",
                "topic": "",
                "token": "",
            },
        }
        cfg = CobotsConfig.from_dict(data)
        self.assertEqual(cfg.workspace_name, "")

    def test_empty_dict_workspace_name_default(self) -> None:
        cfg = CobotsConfig.from_dict({})
        self.assertEqual(cfg.workspace_name, "")

    def test_empty_yaml_workspace_name_default(self) -> None:
        cfg = CobotsConfig.from_yaml("")
        self.assertEqual(cfg.workspace_name, "")


class TestCobotsConfigWorkspaceNameYamlRoundTrip(unittest.TestCase):
    """Verify YAML serialization round-trips preserve workspace_name."""

    def test_round_trip_with_default_workspace_name(self) -> None:
        original = CobotsConfig()
        yaml_text = original.to_yaml()
        restored = CobotsConfig.from_yaml(yaml_text)
        self.assertEqual(original.to_dict(), restored.to_dict())

    def test_round_trip_with_custom_workspace_name(self) -> None:
        original = CobotsConfig(workspace_name="my-cool-project")
        yaml_text = original.to_yaml()
        restored = CobotsConfig.from_yaml(yaml_text)
        self.assertEqual(original.to_dict(), restored.to_dict())
        self.assertEqual(restored.workspace_name, "my-cool-project")


class TestCobotsConfigWorkspaceNameFileRoundTrip(unittest.TestCase):
    """Verify file-based serialization round-trips preserve
    workspace_name.
    """

    def test_write_and_read_file_with_workspace_name(self) -> None:
        original = CobotsConfig(workspace_name="file-test-project")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as fh:
            tmp_path = fh.name

        try:
            original.write_file(tmp_path)
            restored = CobotsConfig.from_file(tmp_path)
            self.assertEqual(original.to_dict(), restored.to_dict())
            self.assertEqual(restored.workspace_name, "file-test-project")
        finally:
            os.unlink(tmp_path)

    def test_read_legacy_file_without_workspace_name(self) -> None:
        """Write a config file that predates workspace_name, then
        load it.
        """
        legacy_yaml = (
            "task_status_values:\n"
            "- pending\n"
            "- underway\n"
            "- done\n"
            "- abandoned\n"
            "task_id_length: 16\n"
            "report_id_length: 16\n"
            "ntfy:\n"
            "  url: https://ntfy.sh\n"
            "  topic: ''\n"
            "  token: ''\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False,
        ) as fh:
            fh.write(legacy_yaml)
            tmp_path = fh.name

        try:
            cfg = CobotsConfig.from_file(tmp_path)
            self.assertEqual(cfg.workspace_name, "")
            # Existing fields should still be intact.
            self.assertEqual(
                cfg.task_status_values,
                ["pending", "underway", "done", "abandoned"],
            )
        finally:
            os.unlink(tmp_path)


class TestCobotsConfigReprTokenMasking(unittest.TestCase):
    """Verify `CobotsConfig.__repr__` masks the ntfy token."""

    def test_repr_masks_nonempty_token(self) -> None:
        """A non-empty token must be replaced with '***' in repr."""
        ntfy = NtfyConfig(token="tk_super_secret")
        cfg = CobotsConfig(ntfy=ntfy)
        r = repr(cfg)
        self.assertNotIn("tk_super_secret", r)
        self.assertIn("***", r)

    def test_repr_empty_token_not_masked(self) -> None:
        """An empty token should appear as-is (no '***')."""
        cfg = CobotsConfig(ntfy=NtfyConfig(token=""))
        r = repr(cfg)
        self.assertNotIn("***", r)

    def test_repr_contains_class_name(self) -> None:
        cfg = CobotsConfig()
        self.assertTrue(repr(cfg).startswith("CobotsConfig("))


# ===================================================================
# CobotsConfig tests (knowledge_id_length)
# ===================================================================


class TestCobotsConfigKnowledgeIdLength(unittest.TestCase):
    """Verify the `knowledge_id_length` field defaults and round-trips."""

    def test_default_value(self) -> None:
        cfg = CobotsConfig()
        self.assertEqual(
            cfg.knowledge_id_length,
            CobotsConfig.DEFAULT_KNOWLEDGE_ID_LENGTH,
        )
        self.assertEqual(cfg.knowledge_id_length, 16)

    def test_custom_value_preserved(self) -> None:
        cfg = CobotsConfig(knowledge_id_length=24)
        self.assertEqual(cfg.knowledge_id_length, 24)

    def test_included_in_to_dict(self) -> None:
        cfg = CobotsConfig(knowledge_id_length=12)
        self.assertEqual(cfg.to_dict()["knowledge_id_length"], 12)

    def test_from_dict_reads_value(self) -> None:
        cfg = CobotsConfig.from_dict({"knowledge_id_length": 20})
        self.assertEqual(cfg.knowledge_id_length, 20)

    def test_missing_key_falls_back_to_default(self) -> None:
        # Backward compatibility: legacy config lacking the key uses default.
        cfg = CobotsConfig.from_dict(
            {"task_id_length": 8, "report_id_length": 8}
        )
        self.assertEqual(cfg.knowledge_id_length, 16)

    def test_dict_round_trip(self) -> None:
        original = CobotsConfig(knowledge_id_length=18)
        restored = CobotsConfig.from_dict(original.to_dict())
        self.assertEqual(restored.knowledge_id_length, 18)

    def test_yaml_round_trip(self) -> None:
        original = CobotsConfig(knowledge_id_length=22)
        restored = CobotsConfig.from_yaml(original.to_yaml())
        self.assertEqual(restored.knowledge_id_length, 22)


if __name__ == "__main__":
    unittest.main()
