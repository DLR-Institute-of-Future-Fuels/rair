"""Tests for auto_discover feature in core.py."""

from pathlib import Path
from rair.config import RairConfig
from rair.core import should_use_auto_discovery_for_input, should_use_auto_discovery_for_output


class TestShouldUseAutoDiscoveryForInput:
    def test_auto_discover_true_with_no_input_glob_and_autodata_dir(self):
        config = RairConfig(
            input_glob=[],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_input(config) is True

    def test_auto_discover_false_with_no_input_glob_and_autodata_dir(self):
        config = RairConfig(
            input_glob=[],
            autodata_dir=Path("data"),
            auto_discover=False,
        )
        assert should_use_auto_discovery_for_input(config) is False

    def test_auto_discover_true_with_input_glob(self):
        config = RairConfig(
            input_glob=["data/*.csv"],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_input(config) is False

    def test_auto_discover_true_without_autodata_dir(self):
        config = RairConfig(
            input_glob=[],
            autodata_dir=None,
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_input(config) is False

    def test_auto_discover_default_is_true(self):
        config = RairConfig(
            input_glob=[],
            autodata_dir=Path("data"),
        )
        assert should_use_auto_discovery_for_input(config) is True


class TestShouldUseAutoDiscoveryForOutput:
    def test_auto_discover_true_with_no_output_glob_and_autodata_dir(self):
        config = RairConfig(
            output_glob=[],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_output(config) is True

    def test_auto_discover_false_with_no_output_glob_and_autodata_dir(self):
        config = RairConfig(
            output_glob=[],
            autodata_dir=Path("data"),
            auto_discover=False,
        )
        assert should_use_auto_discovery_for_output(config) is False

    def test_auto_discover_true_with_output_glob(self):
        config = RairConfig(
            output_glob=["results/*.json"],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_output(config) is False

    def test_auto_discover_true_without_autodata_dir(self):
        config = RairConfig(
            output_glob=[],
            autodata_dir=None,
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_output(config) is False

    def test_auto_discover_default_is_true(self):
        config = RairConfig(
            output_glob=[],
            autodata_dir=Path("data"),
        )
        assert should_use_auto_discovery_for_output(config) is True


class TestAutoDiscoverSelectiveMode:
    def test_selective_mode_input_only_disables_input_auto_discover(self):
        config = RairConfig(
            input_glob=["data/*.csv"],
            output_glob=[],
            autodata_dir=Path("data"),
            auto_discover=False,
        )
        assert should_use_auto_discovery_for_input(config) is False
        assert should_use_auto_discovery_for_output(config) is False

    def test_selective_mode_output_only_disables_output_auto_discover(self):
        config = RairConfig(
            input_glob=[],
            output_glob=["results/*.json"],
            autodata_dir=Path("data"),
            auto_discover=False,
        )
        assert should_use_auto_discovery_for_input(config) is False
        assert should_use_auto_discovery_for_output(config) is False

    def test_selective_mode_both_specified(self):
        config = RairConfig(
            input_glob=["data/*.csv"],
            output_glob=["results/*.json"],
            autodata_dir=Path("data"),
            auto_discover=False,
        )
        assert should_use_auto_discovery_for_input(config) is False
        assert should_use_auto_discovery_for_output(config) is False

    def test_mixed_mode_input_specified_output_auto_discover(self):
        config = RairConfig(
            input_glob=["data/*.csv"],
            output_glob=[],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_input(config) is False
        assert should_use_auto_discovery_for_output(config) is True

    def test_mixed_mode_output_specified_input_auto_discover(self):
        config = RairConfig(
            input_glob=[],
            output_glob=["results/*.json"],
            autodata_dir=Path("data"),
            auto_discover=True,
        )
        assert should_use_auto_discovery_for_input(config) is True
        assert should_use_auto_discovery_for_output(config) is False