"""CLI configuration integration for pytest-drill-sergeant."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

from pytest_drill_sergeant.core.config import DrillSergeantConfig

# Threshold constants
MAX_THRESHOLD_VALUE = 100
MIN_THRESHOLD_VALUE = 0

if TYPE_CHECKING:
    from collections.abc import Mapping

    from _pytest.config import Parser


class ConfigError(ValueError):
    """Raised when CLI configuration parsing fails."""


# Raw, pre-validated CLI args (what we currently stuff in a dict[str, object])
class ArgConfigRaw(TypedDict, total=False):
    """Raw CLI configuration dictionary with optional fields."""

    # Direct mappings
    mode: NotRequired[str]
    persona: NotRequired[str]
    sut_package: NotRequired[str | None]
    fail_on_how: NotRequired[bool]
    verbose: NotRequired[bool]
    quiet: NotRequired[bool]
    json_report_path: NotRequired[str | None]
    sarif_report_path: NotRequired[str | None]

    # Rule configuration
    enabled_rules: NotRequired[set[str]]
    suppressed_rules: NotRequired[set[str]]

    # Threshold configuration
    thresholds: NotRequired[dict[str, float]]

    # Budget configuration
    budgets: NotRequired[dict[str, int]]

    # Output configuration
    output_formats: NotRequired[list[str]]

    # Mock configuration
    mock_allowlist: NotRequired[set[str]]
    mock_deny_list: NotRequired[set[str]]


# Small, typed coercion helpers (mypy-friendly)
def _to_bool(v: bool | str | None, *, default: bool) -> bool:
    """Convert value to boolean."""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    msg = f"Invalid boolean: {v!r}"
    raise ConfigError(msg)


def _to_str(v: str | None, *, default: str) -> str:
    """Convert value to string."""
    return str(v) if v is not None else default


def _to_optional_str(v: str | None) -> str | None:
    """Convert value to optional string."""
    return str(v) if v is not None else None


def _to_set_str(v: list[str] | set[str] | str | None, *, default: set[str]) -> set[str]:
    """Convert value to set of strings."""
    if v is None:
        return default
    if isinstance(v, set):
        return v
    if isinstance(v, list):
        return set(v)
    if isinstance(v, str):
        return {item.strip() for item in v.split(",") if item.strip()}
    msg = f"Invalid set format: {v!r}"
    raise ConfigError(msg)


def _to_list_str(v: list[str] | str | None, *, default: list[str]) -> list[str]:
    """Convert value to list of strings."""
    if v is None:
        return default
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    msg = f"Invalid list format: {v!r}"
    raise ConfigError(msg)


def _to_dict_str_float(
    v: dict[str, float] | None, *, default: dict[str, float]
) -> dict[str, float]:
    """Convert value to dict[str, float]."""
    if v is None:
        return default
    if isinstance(v, dict):
        return v
    msg = f"Invalid dict format: {v!r}"
    raise ConfigError(msg)


def _to_dict_str_int(
    v: dict[str, int] | None, *, default: dict[str, int]
) -> dict[str, int]:
    """Convert value to dict[str, int]."""
    if v is None:
        return default
    if isinstance(v, dict):
        return v
    msg = f"Invalid dict format: {v!r}"
    raise ConfigError(msg)


def _extract_thresholds(raw: Mapping[str, object]) -> dict[str, float]:
    """Extract and validate thresholds from raw config."""
    thresholds_raw = cast("dict[str, float] | None", raw.get("thresholds"))
    if thresholds_raw is None:
        return {}

    if not isinstance(thresholds_raw, dict):
        msg = "thresholds must be a dictionary"
        raise ConfigError(msg)

    # Validate threshold values
    for name, value in thresholds_raw.items():
        if not isinstance(value, int | float):
            msg = f"Threshold {name} must be numeric, got {type(value)}"
            raise ConfigError(msg)
        if "threshold" in name and not (
            MIN_THRESHOLD_VALUE <= value <= MAX_THRESHOLD_VALUE
        ):
            msg = f"Threshold {name} must be between 0 and 100, got {value}"
            raise ConfigError(msg)
        if "jaccard" in name and not (0 <= value <= 1):
            msg = f"Jaccard threshold {name} must be between 0 and 1, got {value}"
            raise ConfigError(msg)

    return thresholds_raw


def _extract_budgets(raw: Mapping[str, object]) -> dict[str, int]:
    """Extract and validate budgets from raw config."""
    budgets_raw = cast("dict[str, int] | None", raw.get("budgets"))
    if budgets_raw is None:
        return {}

    if not isinstance(budgets_raw, dict):
        msg = "budgets must be a dictionary"
        raise ConfigError(msg)

    # Validate budget values
    for budget_type, value in budgets_raw.items():
        if not isinstance(value, int):
            msg = f"Budget {budget_type} must be an integer, got {type(value)}"
            raise ConfigError(msg)
        if value < 0:
            msg = f"Budget {budget_type} must be non-negative, got {value}"
            raise ConfigError(msg)

    return budgets_raw


def _extract_basic_mappings(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract basic string mappings."""
    mappings: ArgConfigRaw = {}
    if hasattr(ns, "ds_mode") and ns.ds_mode is not None:
        mappings["mode"] = str(ns.ds_mode)
    if hasattr(ns, "ds_persona") and ns.ds_persona is not None:
        mappings["persona"] = str(ns.ds_persona)
    if hasattr(ns, "ds_sut_package") and ns.ds_sut_package is not None:
        mappings["sut_package"] = str(ns.ds_sut_package)
    return mappings


def _extract_boolean_mappings(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract boolean mappings."""
    mappings: ArgConfigRaw = {}
    if hasattr(ns, "ds_fail_on_how") and ns.ds_fail_on_how is not None:
        mappings["fail_on_how"] = bool(ns.ds_fail_on_how)
    if hasattr(ns, "ds_verbose") and ns.ds_verbose is not None:
        mappings["verbose"] = bool(ns.ds_verbose)
    if hasattr(ns, "ds_quiet") and ns.ds_quiet is not None:
        mappings["quiet"] = bool(ns.ds_quiet)
    return mappings


def _extract_report_mappings(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract report path mappings."""
    mappings: ArgConfigRaw = {}
    if hasattr(ns, "ds_json_report") and ns.ds_json_report is not None:
        mappings["json_report_path"] = str(ns.ds_json_report)
    if hasattr(ns, "ds_sarif_report") and ns.ds_sarif_report is not None:
        mappings["sarif_report_path"] = str(ns.ds_sarif_report)
    return mappings


def _extract_direct_mappings(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract direct argument mappings."""
    mappings: ArgConfigRaw = {}
    mappings.update(_extract_basic_mappings(ns))
    mappings.update(_extract_boolean_mappings(ns))
    mappings.update(_extract_report_mappings(ns))
    return mappings


def _extract_rule_config(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract rule configuration."""
    config: ArgConfigRaw = {}
    if hasattr(ns, "ds_disable_all_rules") and ns.ds_disable_all_rules:
        config["enabled_rules"] = set()
    elif hasattr(ns, "ds_enable_rules") and ns.ds_enable_rules is not None:
        config["enabled_rules"] = set(ns.ds_enable_rules)
    if hasattr(ns, "ds_suppress_rules") and ns.ds_suppress_rules is not None:
        config["suppressed_rules"] = set(ns.ds_suppress_rules)
    return config


def _extract_bis_thresholds(ns: argparse.Namespace) -> dict[str, float]:
    """Extract BIS threshold values."""
    thresholds: dict[str, float] = {}
    if hasattr(ns, "ds_bis_threshold_warn") and ns.ds_bis_threshold_warn is not None:
        thresholds["bis_threshold_warn"] = float(ns.ds_bis_threshold_warn)
    if hasattr(ns, "ds_bis_threshold_fail") and ns.ds_bis_threshold_fail is not None:
        thresholds["bis_threshold_fail"] = float(ns.ds_bis_threshold_fail)
    return thresholds


def _extract_clone_thresholds(ns: argparse.Namespace) -> dict[str, float]:
    """Extract clone threshold values."""
    thresholds: dict[str, float] = {}
    if (
        hasattr(ns, "ds_static_clone_threshold")
        and ns.ds_static_clone_threshold is not None
    ):
        thresholds["static_clone_hamming"] = float(ns.ds_static_clone_threshold)
    if (
        hasattr(ns, "ds_dynamic_clone_threshold")
        and ns.ds_dynamic_clone_threshold is not None
    ):
        thresholds["dynamic_cov_jaccard"] = float(ns.ds_dynamic_clone_threshold)
    return thresholds


def _extract_mock_thresholds(ns: argparse.Namespace) -> dict[str, float]:
    """Extract mock threshold values."""
    thresholds: dict[str, float] = {}
    if (
        hasattr(ns, "ds_mock_assert_threshold")
        and ns.ds_mock_assert_threshold is not None
    ):
        thresholds["mock_assert_threshold"] = float(ns.ds_mock_assert_threshold)
    return thresholds


def _extract_threshold_config(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract threshold configuration."""
    thresholds: dict[str, float] = {}
    thresholds.update(_extract_bis_thresholds(ns))
    thresholds.update(_extract_clone_thresholds(ns))
    thresholds.update(_extract_mock_thresholds(ns))

    config: ArgConfigRaw = {}
    if thresholds:
        config["thresholds"] = thresholds
    return config


def _extract_budget_config(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract budget configuration."""
    budgets: dict[str, int] = {}
    if hasattr(ns, "ds_warn_budget") and ns.ds_warn_budget is not None:
        budgets["warn"] = int(ns.ds_warn_budget)
    if hasattr(ns, "ds_error_budget") and ns.ds_error_budget is not None:
        budgets["error"] = int(ns.ds_error_budget)
    config: ArgConfigRaw = {}
    if budgets:
        config["budgets"] = budgets
    return config


def _extract_output_config(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract output configuration."""
    config: ArgConfigRaw = {}
    if hasattr(ns, "ds_output_formats") and ns.ds_output_formats is not None:
        config["output_formats"] = list(ns.ds_output_formats)
    return config


def _extract_mock_config(ns: argparse.Namespace) -> ArgConfigRaw:
    """Extract mock configuration."""
    config: ArgConfigRaw = {}
    if hasattr(ns, "ds_mock_allowlist") and ns.ds_mock_allowlist is not None:
        config["mock_allowlist"] = set(ns.ds_mock_allowlist)
    if hasattr(ns, "ds_mock_deny_list") and ns.ds_mock_deny_list is not None:
        config["mock_deny_list"] = set(ns.ds_mock_deny_list)
    return config


def namespace_to_raw(ns: argparse.Namespace) -> ArgConfigRaw:
    """Convert argparse Namespace to typed raw config."""
    raw: ArgConfigRaw = {}

    # Extract different configuration sections
    raw.update(_extract_direct_mappings(ns))
    raw.update(_extract_rule_config(ns))
    raw.update(_extract_threshold_config(ns))
    raw.update(_extract_budget_config(ns))
    raw.update(_extract_output_config(ns))
    raw.update(_extract_mock_config(ns))

    return raw


def build_config_from_mapping(raw: Mapping[str, object]) -> DrillSergeantConfig:
    """Build DrillSergeantConfig from raw mapping with proper type coercion."""
    # Extract and coerce each field with proper validation
    mode = _to_str(cast("str | None", raw.get("mode")), default="advisory")
    persona = _to_str(cast("str | None", raw.get("persona")), default="drill_sergeant")
    sut_package = _to_optional_str(cast("str | None", raw.get("sut_package")))
    fail_on_how = _to_bool(cast("bool | None", raw.get("fail_on_how")), default=False)
    verbose = _to_bool(cast("bool | None", raw.get("verbose")), default=False)
    quiet = _to_bool(cast("bool | None", raw.get("quiet")), default=False)
    json_report_path = _to_optional_str(cast("str | None", raw.get("json_report_path")))
    sarif_report_path = _to_optional_str(
        cast("str | None", raw.get("sarif_report_path"))
    )

    enabled_rules = _to_set_str(
        cast("set[str] | list[str] | None", raw.get("enabled_rules")), default=set()
    )
    suppressed_rules = _to_set_str(
        cast("set[str] | list[str] | None", raw.get("suppressed_rules")), default=set()
    )

    thresholds = _extract_thresholds(raw)
    budgets = _extract_budgets(raw)

    output_formats = _to_list_str(
        cast("list[str] | str | None", raw.get("output_formats")), default=["terminal"]
    )

    mock_allowlist = _to_set_str(
        cast("set[str] | list[str] | str | None", raw.get("mock_allowlist")),
        default=set(),
    )

    # Validate consistency
    if verbose and quiet:
        msg = "Cannot specify both --ds-verbose and --ds-quiet"
        raise ConfigError(msg)

    return DrillSergeantConfig(
        mode=mode,
        persona=persona,
        sut_package=sut_package,
        fail_on_how=fail_on_how,
        verbose=verbose,
        quiet=quiet,
        json_report_path=json_report_path,
        sarif_report_path=sarif_report_path,
        enabled_rules=enabled_rules,
        suppressed_rules=suppressed_rules,
        thresholds=thresholds,
        budgets=budgets,
        output_formats=output_formats,
        mock_allowlist=mock_allowlist,
    )


class DrillSergeantArgumentParser:
    """Argument parser for drill sergeant CLI options."""

    def __init__(self) -> None:
        """Initialize the argument parser."""
        self.parser = argparse.ArgumentParser(
            description="pytest-drill-sergeant: AI test quality enforcement",
            add_help=False,  # We'll add help manually
        )
        self._setup_arguments()

    def _setup_arguments(self) -> None:
        """Set up all command line arguments."""
        # Main group
        main_group = self.parser.add_argument_group("Main Options")
        main_group.add_argument(
            "--ds-mode",
            choices=["advisory", "quality-gate", "strict"],
            default="advisory",
            help="Drill sergeant mode (default: advisory)",
        )
        main_group.add_argument(
            "--ds-persona",
            default="drill_sergeant",
            help="Persona to use for feedback (default: drill_sergeant)",
        )
        main_group.add_argument(
            "--ds-sut-package", help="System under test package name"
        )

        # Analysis options
        analysis_group = self.parser.add_argument_group("Analysis Options")
        analysis_group.add_argument(
            "--ds-fail-on-how",
            action="store_true",
            help="Fail tests with low BIS scores",
        )
        analysis_group.add_argument(
            "--ds-verbose", action="store_true", help="Enable verbose output"
        )
        analysis_group.add_argument(
            "--ds-quiet", action="store_true", help="Enable quiet output"
        )

        # Rule configuration
        rules_group = self.parser.add_argument_group("Rule Configuration")
        rules_group.add_argument(
            "--ds-enable-rules", nargs="+", help="Enable specific rules"
        )
        rules_group.add_argument(
            "--ds-suppress-rules", nargs="+", help="Suppress specific rules"
        )
        rules_group.add_argument(
            "--ds-disable-all-rules", action="store_true", help="Disable all rules"
        )

        # Threshold configuration
        threshold_group = self.parser.add_argument_group("Threshold Configuration")
        threshold_group.add_argument(
            "--ds-bis-threshold-warn", type=float, help="BIS warning threshold (0-100)"
        )
        threshold_group.add_argument(
            "--ds-bis-threshold-fail", type=float, help="BIS failure threshold (0-100)"
        )
        threshold_group.add_argument(
            "--ds-static-clone-threshold",
            type=int,
            help="Static clone similarity threshold (hamming distance)",
        )
        threshold_group.add_argument(
            "--ds-dynamic-clone-threshold",
            type=float,
            help="Dynamic clone similarity threshold (jaccard index)",
        )
        threshold_group.add_argument(
            "--ds-mock-assert-threshold",
            type=int,
            help="Mock assertion count threshold",
        )

        # Budget configuration
        budget_group = self.parser.add_argument_group("Budget Configuration")
        budget_group.add_argument(
            "--ds-warn-budget",
            type=int,
            help="Warning budget (number of warnings allowed)",
        )
        budget_group.add_argument(
            "--ds-error-budget",
            type=int,
            help="Error budget (number of errors allowed)",
        )

        # Output options
        output_group = self.parser.add_argument_group("Output Options")
        output_group.add_argument("--ds-json-report", help="Path to JSON report output")
        output_group.add_argument(
            "--ds-sarif-report", help="Path to SARIF report output"
        )
        output_group.add_argument(
            "--ds-output-formats",
            nargs="+",
            choices=["terminal", "json", "sarif"],
            help="Output formats to generate",
        )

        # Mock configuration
        mock_group = self.parser.add_argument_group("Mock Configuration")
        mock_group.add_argument(
            "--ds-mock-allowlist",
            nargs="+",
            help="Additional patterns to allow in mocks",
        )
        mock_group.add_argument(
            "--ds-mock-deny-list", nargs="+", help="Patterns to deny in mocks"
        )

        # Help
        self.parser.add_argument(
            "--ds-help", action="help", help="Show this help message and exit"
        )

    def parse_args(self, args: list[str] | None = None) -> dict[str, object]:
        """Parse command line arguments.

        Args:
            args: Command line arguments (defaults to sys.argv)

        Returns:
            Dictionary of parsed arguments
        """
        parsed_args = self.parser.parse_args(args)
        raw_config = namespace_to_raw(parsed_args)
        return cast("dict[str, object]", raw_config)

    def add_pytest_options(self, pytest_parser: Parser) -> None:
        """Add drill sergeant options to pytest parser.

        Args:
            pytest_parser: Pytest argument parser
        """
        group = pytest_parser.getgroup("drill-sergeant")

        # Add all our options to the pytest group
        # Note: _actions is a standard argparse.ArgumentParser attribute
        for action in self.parser._actions:  # noqa: SLF001
            if action.dest.startswith("ds_"):
                # Prepare kwargs for addoption
                kwargs = {
                    "dest": action.dest,
                    "default": action.default,
                    "help": action.help,
                }

                # Add optional parameters
                if action.nargs is not None and action.nargs != 0:
                    kwargs["nargs"] = action.nargs
                if action.const is not None and action.nargs == "?":
                    kwargs["const"] = action.const
                if action.type is not None:
                    kwargs["type"] = action.type
                if action.choices is not None:
                    kwargs["choices"] = action.choices
                if action.metavar is not None:
                    kwargs["metavar"] = action.metavar

                # Add option directly to pytest group
                group.addoption(*action.option_strings, **kwargs)


def parse_cli_args(args: list[str] | None = None) -> dict[str, object]:
    """Parse command line arguments for drill sergeant.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Dictionary of parsed arguments
    """
    parser = DrillSergeantArgumentParser()
    return parser.parse_args(args)


def create_pytest_config_from_args(args: dict[str, object]) -> DrillSergeantConfig:
    """Create a configuration from CLI arguments.

    Args:
        args: Parsed CLI arguments

    Returns:
        Configuration object
    """
    return build_config_from_mapping(args)


def _validate_verbose_quiet_conflict(args: dict[str, object]) -> list[str]:
    """Validate verbose/quiet conflict."""
    errors = []
    verbose = args.get("verbose", False)
    quiet = args.get("quiet", False)
    if verbose and quiet:
        errors.append("Cannot specify both --ds-verbose and --ds-quiet")
    return errors


def _validate_thresholds_in_args(args: dict[str, object]) -> list[str]:
    """Validate thresholds in args."""
    errors = []
    thresholds_raw = args.get("thresholds")
    if isinstance(thresholds_raw, dict):
        for name, value in thresholds_raw.items():
            if not isinstance(value, int | float):
                errors.append(f"Threshold {name} must be numeric, got {type(value)}")
            elif "threshold" in name and not (
                MIN_THRESHOLD_VALUE <= value <= MAX_THRESHOLD_VALUE
            ):
                errors.append(
                    f"Threshold {name} must be between 0 and 100, got {value}"
                )
            elif "jaccard" in name and not (0 <= value <= 1):
                errors.append(
                    f"Jaccard threshold {name} must be between 0 and 1, got {value}"
                )
    return errors


def _validate_budgets_in_args(args: dict[str, object]) -> list[str]:
    """Validate budgets in args."""
    errors = []
    budgets_raw = args.get("budgets")
    if isinstance(budgets_raw, dict):
        for budget_type, value in budgets_raw.items():
            if not isinstance(value, int):
                errors.append(
                    f"Budget {budget_type} must be an integer, got {type(value)}"
                )
            elif value < 0:
                errors.append(f"Budget {budget_type} must be non-negative, got {value}")
    return errors


def validate_cli_args(args: dict[str, object]) -> list[str]:
    """Validate CLI arguments and return any errors.

    Args:
        args: Parsed CLI arguments

    Returns:
        List of validation errors
    """
    errors = []
    errors.extend(_validate_verbose_quiet_conflict(args))
    errors.extend(_validate_thresholds_in_args(args))
    errors.extend(_validate_budgets_in_args(args))
    return errors
