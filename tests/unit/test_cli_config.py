"""Tests for the CLI configuration system."""

import argparse
from unittest.mock import MagicMock, patch

from pytest_drill_sergeant.core.cli_config import (
    DrillSergeantArgumentParser,
    create_pytest_config_from_args,
    namespace_to_raw,
    parse_cli_args,
    validate_cli_args,
)
from tests.constants import (
    BIS_THRESHOLD_FAIL,
    BIS_THRESHOLD_WARN,
    BUDGET_ERROR,
    BUDGET_WARN,
    DYNAMIC_COV_JACCARD,
    EXPECTED_ERROR_COUNT_2,
    EXPECTED_ERROR_COUNT_3,
    MOCK_ASSERT_THRESHOLD,
    STATIC_CLONE_HAMMING,
)


class TestDrillSergeantArgumentParser:
    """Test the DrillSergeantArgumentParser class."""

    def test_parser_creation(self) -> None:
        """Test argument parser creation."""
        parser = DrillSergeantArgumentParser()

        assert parser.parser is not None
        # When run under pytest, the program name gets changed to "pytest"
        # When run as a module, it might be "__main__.py"
        assert parser.parser.prog in ["pytest-drill-sergeant", "pytest", "__main__.py"]

    def test_parse_args_basic(self) -> None:
        """Test basic argument parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(["--ds-mode", "strict", "--ds-persona", "snoop_dogg"])

        assert args["mode"] == "strict"
        assert args["persona"] == "snoop_dogg"

    def test_parse_args_boolean_flags(self) -> None:
        """Test boolean flag parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(["--ds-verbose", "--ds-fail-on-how", "--ds-quiet"])

        assert args["verbose"] is True
        assert args["fail_on_how"] is True
        assert args["quiet"] is True

    def test_parse_args_rules(self) -> None:
        """Test rule configuration parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(
            [
                "--ds-enable-rules",
                "aaa_comments",
                "private_access",
                "--ds-suppress-rules",
                "private_access",
                "--ds-disable-all-rules",
            ]
        )

        # disable_all_rules overrides enable_rules, setting enabled_rules to empty set
        assert args["enabled_rules"] == set()
        assert args["suppressed_rules"] == {"private_access"}

    def test_parse_args_thresholds(self) -> None:
        """Test threshold configuration parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(
            [
                "--ds-bis-threshold-warn",
                "85",
                "--ds-bis-threshold-fail",
                "65",
                "--ds-static-clone-threshold",
                "8",
                "--ds-dynamic-clone-threshold",
                "0.9",
                "--ds-mock-assert-threshold",
                "10",
            ]
        )

        assert "thresholds" in args
        thresholds = args["thresholds"]
        assert isinstance(thresholds, dict)
        thresholds_dict: dict[str, int | float] = thresholds
        assert thresholds_dict["bis_threshold_warn"] == BIS_THRESHOLD_WARN
        assert thresholds_dict["bis_threshold_fail"] == BIS_THRESHOLD_FAIL
        assert thresholds_dict["static_clone_hamming"] == STATIC_CLONE_HAMMING
        assert thresholds_dict["dynamic_cov_jaccard"] == DYNAMIC_COV_JACCARD
        assert thresholds_dict["mock_assert_threshold"] == MOCK_ASSERT_THRESHOLD

    def test_parse_args_budgets(self) -> None:
        """Test budget configuration parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(["--ds-warn-budget", "20", "--ds-error-budget", "5"])

        assert "budgets" in args
        budgets = args["budgets"]
        assert isinstance(budgets, dict)
        budgets_dict: dict[str, int | float] = budgets
        assert budgets_dict["warn"] == BUDGET_WARN
        assert budgets_dict["error"] == BUDGET_ERROR

    def test_parse_args_output(self) -> None:
        """Test output configuration parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(
            [
                "--ds-json-report",
                "/tmp/report.json",
                "--ds-sarif-report",
                "/tmp/report.sarif",
                "--ds-output-formats",
                "terminal",
                "json",
                "sarif",
            ]
        )

        assert args["json_report_path"] == "/tmp/report.json"
        assert args["sarif_report_path"] == "/tmp/report.sarif"
        assert args["output_formats"] == ["terminal", "json", "sarif"]

    def test_parse_args_mock_config(self) -> None:
        """Test mock configuration parsing."""
        parser = DrillSergeantArgumentParser()

        args = parser.parse_args(
            [
                "--ds-mock-allowlist",
                "custom.*",
                "test.*",
                "--ds-mock-deny-list",
                "internal.*",
                "private.*",
            ]
        )

        assert args["mock_allowlist"] == {"custom.*", "test.*"}
        assert args["mock_deny_list"] == {"internal.*", "private.*"}

    def test_convert_args_to_config(self) -> None:
        """Test argument to configuration conversion."""

        # Create a mock parsed args object
        class MockArgs(argparse.Namespace):
            def __init__(self) -> None:
                super().__init__()
                self.ds_mode = "strict"
                self.ds_persona = "snoop_dogg"
                self.ds_sut_package = "myapp"
                self.ds_fail_on_how = True
                self.ds_verbose = True
                self.ds_quiet = False
                self.ds_json_report = "/tmp/report.json"
                self.ds_sarif_report = "/tmp/report.sarif"
                self.ds_enable_rules = ["aaa_comments", "private_access"]
                self.ds_suppress_rules = ["private_access"]
                self.ds_disable_all_rules = False
                self.ds_bis_threshold_warn = 85
                self.ds_bis_threshold_fail = 65
                self.ds_static_clone_threshold = 8
                self.ds_dynamic_clone_threshold = 0.9
                self.ds_mock_assert_threshold = 10
                self.ds_warn_budget = 20
                self.ds_error_budget = 5
                self.ds_output_formats = ["terminal", "json"]
                self.ds_mock_allowlist = ["custom.*", "test.*"]
                self.ds_mock_deny_list = ["internal.*"]

        mock_args = MockArgs()
        config = namespace_to_raw(mock_args)

        assert config["mode"] == "strict"
        assert config["persona"] == "snoop_dogg"
        assert config["sut_package"] == "myapp"
        assert config["fail_on_how"] is True
        assert config["verbose"] is True
        assert config["quiet"] is False
        assert config["json_report_path"] == "/tmp/report.json"
        assert config["sarif_report_path"] == "/tmp/report.sarif"
        assert config["enabled_rules"] == {"aaa_comments", "private_access"}
        assert config["suppressed_rules"] == {"private_access"}
        # Type assertions for nested dictionaries
        thresholds = config.get("thresholds", {})
        assert isinstance(thresholds, dict)
        thresholds_dict: dict[str, int | float] = thresholds
        assert thresholds_dict["bis_threshold_warn"] == BIS_THRESHOLD_WARN
        assert thresholds_dict["bis_threshold_fail"] == BIS_THRESHOLD_FAIL
        assert thresholds_dict["static_clone_hamming"] == STATIC_CLONE_HAMMING
        assert thresholds_dict["dynamic_cov_jaccard"] == DYNAMIC_COV_JACCARD
        assert thresholds_dict["mock_assert_threshold"] == MOCK_ASSERT_THRESHOLD

        budgets = config.get("budgets", {})
        assert isinstance(budgets, dict)
        budgets_dict: dict[str, int] = budgets
        assert budgets_dict["warn"] == BUDGET_WARN
        assert budgets_dict["error"] == BUDGET_ERROR
        assert config["output_formats"] == ["terminal", "json"]
        assert config["mock_allowlist"] == {"custom.*", "test.*"}
        assert config["mock_deny_list"] == {"internal.*"}

    def test_add_pytest_options(self) -> None:
        """Test adding options to pytest parser."""
        parser = DrillSergeantArgumentParser()

        # Create a mock pytest parser
        mock_pytest_parser = MagicMock()
        mock_group = MagicMock()
        mock_pytest_parser.getgroup.return_value = mock_group

        parser.add_pytest_options(mock_pytest_parser)

        # Verify that getgroup was called
        mock_pytest_parser.getgroup.assert_called_once_with("drill-sergeant")

        # Verify that actions were added to the group
        assert mock_group.addoption.called


class TestParseCliArgsFunction:
    """Test the parse_cli_args convenience function."""

    def test_parse_cli_args_basic(self) -> None:
        """Test basic CLI argument parsing."""
        args = parse_cli_args(["--ds-mode", "strict", "--ds-persona", "snoop_dogg"])

        assert args["mode"] == "strict"
        assert args["persona"] == "snoop_dogg"

    def test_parse_cli_args_no_args(self) -> None:
        """Test CLI argument parsing with no arguments."""
        args = parse_cli_args([])

        # Should return empty dict or defaults
        assert isinstance(args, dict)

    def test_parse_cli_args_none(self) -> None:
        """Test CLI argument parsing with None (uses sys.argv)."""
        with patch("sys.argv", ["script.py", "--ds-mode", "advisory"]):
            args = parse_cli_args(None)

            assert args["mode"] == "advisory"


class TestCreatePytestConfigFromArgs:
    """Test the create_pytest_config_from_args function."""

    def test_create_pytest_config_from_args(self) -> None:
        """Test creating pytest config from arguments."""
        args: dict[str, object] = {
            "mode": "strict",
            "persona": "snoop_dogg",
            "verbose": True,
            "budgets": {"warn": 20, "error": 5},
        }

        with patch(
            "pytest_drill_sergeant.core.cli_config.DrillSergeantConfig"
        ) as mock_config_class:
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config

            result = create_pytest_config_from_args(args)

            assert result is mock_config
            # The new implementation provides defaults for all fields
            expected_call: dict[str, object] = {
                "mode": "strict",
                "persona": "snoop_dogg",
                "sut_package": None,
                "fail_on_how": False,
                "verbose": True,
                "quiet": False,
                "json_report_path": None,
                "sarif_report_path": None,
                "enabled_rules": set(),
                "suppressed_rules": set(),
                "thresholds": {},
                "budgets": {"warn": 20, "error": 5},
                "output_formats": ["terminal"],
                "mock_allowlist": set(),
            }
            mock_config_class.assert_called_once_with(**expected_call)


class TestValidateCliArgs:
    """Test the validate_cli_args function."""

    def test_validate_cli_args_valid(self) -> None:
        """Test validation with valid arguments."""
        args: dict[str, object] = {
            "mode": "strict",
            "persona": "snoop_dogg",
            "verbose": True,
            "quiet": False,
            "thresholds": {
                "bis_threshold_warn": 85,
                "bis_threshold_fail": 65,
                "dynamic_cov_jaccard": 0.9,
            },
            "budgets": {"warn": 20, "error": 5},
        }

        errors = validate_cli_args(args)

        assert errors == []

    def test_validate_cli_args_conflicting_verbose_quiet(self) -> None:
        """Test validation with conflicting verbose and quiet."""
        args: dict[str, object] = {"verbose": True, "quiet": True}

        errors = validate_cli_args(args)

        assert len(errors) == 1
        assert "Cannot specify both --ds-verbose and --ds-quiet" in errors[0]

    def test_validate_cli_args_invalid_thresholds(self) -> None:
        """Test validation with invalid thresholds."""
        args: dict[str, object] = {
            "thresholds": {
                "bis_threshold_warn": 150,  # Invalid: > 100
                "dynamic_cov_jaccard": 1.5,  # Invalid: > 1
            }
        }

        errors = validate_cli_args(args)

        assert len(errors) == EXPECTED_ERROR_COUNT_2
        assert any("must be between 0 and 100" in error for error in errors)
        assert any("must be between 0 and 1" in error for error in errors)

    def test_validate_cli_args_negative_budgets(self) -> None:
        """Test validation with negative budgets."""
        args: dict[str, object] = {
            "budgets": {"warn": -5, "error": 10}
        }  # Invalid: negative

        errors = validate_cli_args(args)

        assert len(errors) == 1
        assert "Budget warn must be non-negative" in errors[0]

    def test_validate_cli_args_empty_args(self) -> None:
        """Test validation with empty arguments."""
        args: dict[str, object] = {}

        errors = validate_cli_args(args)

        assert errors == []

    def test_validate_cli_args_mixed_errors(self) -> None:
        """Test validation with multiple types of errors."""
        args: dict[str, object] = {
            "verbose": True,
            "quiet": True,
            "thresholds": {"bis_threshold_warn": 150},
            "budgets": {"warn": -5},
        }

        errors = validate_cli_args(args)

        assert len(errors) == EXPECTED_ERROR_COUNT_3
        assert any("Cannot specify both" in error for error in errors)
        assert any("must be between 0 and 100" in error for error in errors)
        assert any("must be non-negative" in error for error in errors)
