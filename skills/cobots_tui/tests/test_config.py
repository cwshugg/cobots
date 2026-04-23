"""
test_config.py - Unit tests for the config loader.

Tests the thin wrapper that loads StatusConfig from CobotsConfig.
"""

import os
import tempfile
import unittest

from cobots_lib.workspace.config import CobotsConfig, StatusConfig
from config import load_status_config
from tests.helpers import create_mock_workspace

# Import clamp_cli_args from the hyphen-named CLI module.
import importlib
_cobots_tui_cli = importlib.import_module("cobots-tui")
clamp_cli_args = _cobots_tui_cli.clamp_cli_args


class TestLoadStatusConfigDefaults(unittest.TestCase):
    """load_status_config returns defaults when no config file exists."""

    def test_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Point to a non-existent workspace — should get defaults.
            ws = os.path.join(tmp, ".cobots")
            os.makedirs(ws)
            status_config, cobots_config = load_status_config(ws)

            self.assertEqual(status_config.refresh_rate, 5)
            self.assertEqual(status_config.activity_count, 20)


class TestLoadStatusConfigFromFile(unittest.TestCase):
    """load_status_config reads values from a real cobots-config.yaml."""

    def test_reads_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = create_mock_workspace(tmp)
            status_config, cobots_config = load_status_config(ws)

            self.assertEqual(status_config.refresh_rate, 5)
            self.assertEqual(cobots_config.workspace_name, "test-workspace")


class TestStatusConfigRoundTrip(unittest.TestCase):
    """StatusConfig survives a dict round-trip."""

    def test_round_trip(self) -> None:
        original = StatusConfig(refresh_rate=10, activity_count=50)
        d = original.to_dict()
        restored = StatusConfig.from_dict(d)

        self.assertEqual(restored.refresh_rate, 10)
        self.assertEqual(restored.activity_count, 50)


class TestStatusConfigClamping(unittest.TestCase):
    """StatusConfig clamps out-of-range values."""

    def test_refresh_rate_clamped_low(self) -> None:
        cfg = StatusConfig(refresh_rate=0)
        self.assertEqual(cfg.refresh_rate, StatusConfig.MIN_REFRESH_RATE)

    def test_refresh_rate_clamped_high(self) -> None:
        cfg = StatusConfig(refresh_rate=99999)
        self.assertEqual(cfg.refresh_rate, StatusConfig.MAX_REFRESH_RATE)

    def test_activity_count_clamped_low(self) -> None:
        cfg = StatusConfig(activity_count=-5)
        self.assertEqual(cfg.activity_count, StatusConfig.MIN_ACTIVITY_COUNT)

    def test_activity_count_clamped_high(self) -> None:
        cfg = StatusConfig(activity_count=9999)
        self.assertEqual(cfg.activity_count, StatusConfig.MAX_ACTIVITY_COUNT)


class TestCobotsConfigIncludesStatus(unittest.TestCase):
    """CobotsConfig round-trip preserves the status section."""

    def test_round_trip(self) -> None:
        original = CobotsConfig(
            status=StatusConfig(refresh_rate=10, activity_count=30),
        )
        d = original.to_dict()
        restored = CobotsConfig.from_dict(d)

        self.assertEqual(restored.status.refresh_rate, 10)
        self.assertEqual(restored.status.activity_count, 30)


class TestStatusConfigNonNumericValues(unittest.TestCase):
    """StatusConfig gracefully handles non-numeric YAML values.

    Addresses security finding F4: int() cast on non-numeric values
    should fall back to defaults instead of crashing.
    """

    def test_string_refresh_rate_falls_back_to_default(self) -> None:
        cfg = StatusConfig(refresh_rate="fast")
        self.assertEqual(cfg.refresh_rate, StatusConfig.DEFAULT_REFRESH_RATE)

    def test_string_activity_count_falls_back_to_default(self) -> None:
        cfg = StatusConfig(activity_count="many")
        self.assertEqual(cfg.activity_count, StatusConfig.DEFAULT_ACTIVITY_COUNT)

    def test_none_values_use_defaults(self) -> None:
        cfg = StatusConfig()
        self.assertEqual(cfg.refresh_rate, StatusConfig.DEFAULT_REFRESH_RATE)
        self.assertEqual(cfg.activity_count, StatusConfig.DEFAULT_ACTIVITY_COUNT)

    def test_float_string_falls_back_to_default(self) -> None:
        cfg = StatusConfig(refresh_rate="3.5")
        # "3.5" cannot be parsed by int(), so it should fall back.
        self.assertEqual(cfg.refresh_rate, StatusConfig.DEFAULT_REFRESH_RATE)

    def test_empty_string_falls_back_to_default(self) -> None:
        cfg = StatusConfig(refresh_rate="", activity_count="")
        self.assertEqual(cfg.refresh_rate, StatusConfig.DEFAULT_REFRESH_RATE)
        self.assertEqual(cfg.activity_count, StatusConfig.DEFAULT_ACTIVITY_COUNT)

    def test_from_yaml_with_string_values(self) -> None:
        """StatusConfig doesn't crash when YAML contains non-numeric values."""
        config = CobotsConfig.from_yaml("""
status:
  refresh_rate: "fast"
  activity_count: "lots"
""")
        self.assertEqual(config.status.refresh_rate, StatusConfig.DEFAULT_REFRESH_RATE)
        self.assertEqual(config.status.activity_count, StatusConfig.DEFAULT_ACTIVITY_COUNT)


class TestCliArgsClamping(unittest.TestCase):
    """CLI args are clamped to the same bounds as StatusConfig.

    Addresses security finding F3: --refresh-rate and --activity-count
    bypass StatusConfig bounds clamping when explicitly provided.

    Calls the real ``clamp_cli_args()`` from ``cobots-tui.py`` instead
    of reimplementing the clamping logic inline.
    """

    def _make_args(self, **overrides) -> "argparse.Namespace":
        import argparse
        defaults = dict(
            refresh_rate=None,
            activity_count=None,
            show_overview=False,
            no_refresh=False,
            workspace_path=None,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_refresh_rate_clamped_low_via_main(self) -> None:
        """--refresh-rate 1 should be clamped to MIN_REFRESH_RATE."""
        args = self._make_args(refresh_rate=1)
        clamp_cli_args(args, StatusConfig())
        self.assertEqual(args.refresh_rate, StatusConfig.MIN_REFRESH_RATE)

    def test_refresh_rate_clamped_high_via_main(self) -> None:
        """--refresh-rate 99999 should be clamped to MAX_REFRESH_RATE."""
        args = self._make_args(refresh_rate=99999)
        clamp_cli_args(args, StatusConfig())
        self.assertEqual(args.refresh_rate, StatusConfig.MAX_REFRESH_RATE)

    def test_activity_count_clamped_low_via_main(self) -> None:
        """--activity-count 0 should be clamped to MIN_ACTIVITY_COUNT."""
        args = self._make_args(activity_count=0)
        clamp_cli_args(args, StatusConfig())
        self.assertEqual(args.activity_count, StatusConfig.MIN_ACTIVITY_COUNT)

    def test_activity_count_clamped_high_via_main(self) -> None:
        """--activity-count 999999 should be clamped to MAX_ACTIVITY_COUNT."""
        args = self._make_args(activity_count=999999)
        clamp_cli_args(args, StatusConfig())
        self.assertEqual(args.activity_count, StatusConfig.MAX_ACTIVITY_COUNT)

    def test_in_range_values_unchanged(self) -> None:
        """Values within bounds should pass through unchanged."""
        args = self._make_args(refresh_rate=30, activity_count=50)
        clamp_cli_args(args, StatusConfig())
        self.assertEqual(args.refresh_rate, 30)
        self.assertEqual(args.activity_count, 50)

    def test_none_values_use_config_defaults(self) -> None:
        """None values should be filled from the StatusConfig defaults."""
        args = self._make_args()
        cfg = StatusConfig(refresh_rate=10, activity_count=25)
        clamp_cli_args(args, cfg)
        self.assertEqual(args.refresh_rate, 10)
        self.assertEqual(args.activity_count, 25)


if __name__ == "__main__":
    unittest.main()
