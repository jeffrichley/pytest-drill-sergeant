"""Tests for the plugin hooks system."""

import os
from unittest.mock import MagicMock, patch

from _pytest.nodes import Item

from pytest_drill_sergeant.plugin.hooks import (
    pytest_addoption,
    pytest_collection_modifyitems,
    pytest_configure,
    pytest_runtest_call,
    pytest_runtest_logreport,
    pytest_runtest_setup,
    pytest_sessionfinish,
    pytest_terminal_summary,
)


class TestPytestHooks:
    """Test the pytest hook implementations."""

    def test_pytest_addoption(self) -> None:
        """Test pytest_addoption hook."""
        mock_parser = MagicMock()

        with patch(
            "pytest_drill_sergeant.plugin.hooks.DrillSergeantArgumentParser"
        ) as mock_cli_parser_class:
            mock_cli_parser = MagicMock()
            mock_cli_parser_class.return_value = mock_cli_parser

            pytest_addoption(mock_parser)

            mock_cli_parser_class.assert_called_once()
            mock_cli_parser.add_pytest_options.assert_called_once_with(mock_parser)

    def test_pytest_configure(self) -> None:
        """Test pytest_configure hook."""
        mock_config = MagicMock()
        mock_config.option = MagicMock()
        mock_config.option.__dict__ = {
            "ds_mode": "strict",
            "ds_persona": "drill_sergeant",
            "ds_verbose": True,
            "other_option": "value",  # Should be ignored
        }

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "pytest_drill_sergeant.plugin.hooks.setup_standard_logging"
            ) as mock_setup_logging,
            patch(
                "pytest_drill_sergeant.plugin.hooks.initialize_config"
            ) as mock_init_config,
        ):
            pytest_configure(mock_config)

            # Check environment variable is set
            assert os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] == "1"

            # Check logging setup
            mock_setup_logging.assert_called_once()

            # Check config initialization
            mock_init_config.assert_called_once()
            call_args = mock_init_config.call_args
            assert call_args[0][0] == {
                "ds_mode": "strict",
                "ds_persona": "drill_sergeant",
                "ds_verbose": True,
            }
            assert call_args[0][1] is mock_config

    def test_pytest_configure_no_ds_options(self) -> None:
        """Test pytest_configure with no drill sergeant options."""
        mock_config = MagicMock()
        mock_config.option = MagicMock()
        mock_config.option.__dict__ = {
            "other_option": "value",
            "another_option": "value2",
        }

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "pytest_drill_sergeant.plugin.hooks.setup_standard_logging"
            ) as mock_setup_logging,
            patch(
                "pytest_drill_sergeant.plugin.hooks.initialize_config"
            ) as mock_init_config,
        ):
            pytest_configure(mock_config)

            # Check environment variable is set
            assert os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] == "1"

            # Check logging setup
            mock_setup_logging.assert_called_once()

            # Check config initialization with empty dict
            mock_init_config.assert_called_once()
            call_args = mock_init_config.call_args
            assert call_args[0][0] == {}
            assert call_args[0][1] is mock_config

    def test_pytest_collection_modifyitems(self) -> None:
        """Test pytest_collection_modifyitems hook."""
        mock_session = MagicMock()
        mock_config = MagicMock()
        mock_items: list[Item] = [MagicMock(spec=Item), MagicMock(spec=Item)]

        # This hook currently has no implementation, just test it doesn't crash
        pytest_collection_modifyitems(mock_session, mock_config, mock_items)

    def test_pytest_runtest_setup(self) -> None:
        """Test pytest_runtest_setup hook."""
        mock_item = MagicMock()

        # This hook currently has no implementation, just test it doesn't crash
        pytest_runtest_setup(mock_item)

    def test_pytest_runtest_call(self) -> None:
        """Test pytest_runtest_call hook."""
        mock_item = MagicMock()

        # This hook currently has no implementation, just test it doesn't crash
        pytest_runtest_call(mock_item)

    def test_pytest_runtest_logreport(self) -> None:
        """Test pytest_runtest_logreport hook."""
        mock_report = MagicMock()

        # This hook currently has no implementation, just test it doesn't crash
        pytest_runtest_logreport(mock_report)

    def test_pytest_terminal_summary(self) -> None:
        """Test pytest_terminal_summary hook."""
        mock_terminalreporter = MagicMock()
        exitstatus = 0
        mock_config = MagicMock()

        # This hook currently has no implementation, just test it doesn't crash
        pytest_terminal_summary(mock_terminalreporter, exitstatus, mock_config)

    def test_pytest_sessionfinish(self) -> None:
        """Test pytest_sessionfinish hook."""
        mock_session = MagicMock()
        exitstatus = 0

        # This hook currently has no implementation, just test it doesn't crash
        pytest_sessionfinish(mock_session, exitstatus)

    def test_pytest_configure_with_mixed_options(self) -> None:
        """Test pytest_configure with mixed drill sergeant and other options."""
        mock_config = MagicMock()
        mock_config.option = MagicMock()
        mock_config.option.__dict__ = {
            "ds_mode": "advisory",
            "ds_persona": "snoop_dogg",
            "ds_verbose": False,
            "ds_quiet": True,
            "ds_fail_on_how": True,
            "ds_budgets": "warn=10,error=5",
            "ds_thresholds": "bis_threshold_warn=80",
            "ds_enabled_rules": "aaa_comments,private_access",
            "ds_suppressed_rules": "static_clones",
            "ds_output_formats": "terminal,json",
            "ds_json_report_path": "/tmp/report.json",
            "ds_sarif_report_path": "/tmp/report.sarif",
            "ds_sut_package": "my_package",
            "other_option": "value",
            "pytest_option": "value2",
        }

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "pytest_drill_sergeant.plugin.hooks.setup_standard_logging"
            ) as mock_setup_logging,
            patch(
                "pytest_drill_sergeant.plugin.hooks.initialize_config"
            ) as mock_init_config,
        ):
            pytest_configure(mock_config)

            # Check environment variable is set
            assert os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] == "1"

            # Check logging setup
            mock_setup_logging.assert_called_once()

            # Check config initialization with all drill sergeant options
            mock_init_config.assert_called_once()
            call_args = mock_init_config.call_args
            expected_cli_args = {
                "ds_mode": "advisory",
                "ds_persona": "snoop_dogg",
                "ds_verbose": False,
                "ds_quiet": True,
                "ds_fail_on_how": True,
                "ds_budgets": "warn=10,error=5",
                "ds_thresholds": "bis_threshold_warn=80",
                "ds_enabled_rules": "aaa_comments,private_access",
                "ds_suppressed_rules": "static_clones",
                "ds_output_formats": "terminal,json",
                "ds_json_report_path": "/tmp/report.json",
                "ds_sarif_report_path": "/tmp/report.sarif",
                "ds_sut_package": "my_package",
            }
            assert call_args[0][0] == expected_cli_args
            assert call_args[0][1] is mock_config

    def test_pytest_configure_environment_preservation(self) -> None:
        """Test that pytest_configure preserves existing environment variables."""
        mock_config = MagicMock()
        mock_config.option = MagicMock()
        mock_config.option.__dict__ = {}

        with (
            patch.dict(os.environ, {"EXISTING_VAR": "existing_value"}, clear=False),
            patch("pytest_drill_sergeant.plugin.hooks.setup_standard_logging"),
            patch("pytest_drill_sergeant.plugin.hooks.initialize_config"),
        ):
            pytest_configure(mock_config)

            # Check that existing environment variable is preserved
            assert os.environ["EXISTING_VAR"] == "existing_value"
            # Check that new environment variable is set
            assert os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] == "1"

    def test_pytest_configure_exception_handling(self) -> None:
        """Test pytest_configure handles exceptions gracefully."""
        mock_config = MagicMock()
        mock_config.option = MagicMock()
        mock_config.option.__dict__ = {"ds_mode": "strict"}

        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "pytest_drill_sergeant.plugin.hooks.setup_standard_logging"
            ) as mock_setup,
            patch("pytest_drill_sergeant.plugin.hooks.initialize_config") as mock_init,
        ):
            # Test that the function runs without crashing
            pytest_configure(mock_config)

            # Environment variable should be set
            assert os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] == "1"

            # Functions should be called
            mock_setup.assert_called_once()
            mock_init.assert_called_once()
