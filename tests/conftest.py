"""Pytest configuration and fixtures for drill sergeant tests."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pytest_drill_sergeant.core.config import DrillSergeantConfig
from pytest_drill_sergeant.core.config_manager import ConfigManager


@pytest.fixture
def reset_config_manager() -> Generator[None, None, None]:
    """Reset the ConfigManager singleton before each test."""
    ConfigManager._instance = None
    ConfigManager._config = None
    yield
    ConfigManager._instance = None
    ConfigManager._config = None


@pytest.fixture
def default_config() -> DrillSergeantConfig:
    """Create a default DrillSergeantConfig for testing."""
    return DrillSergeantConfig()


@pytest.fixture
def strict_config() -> DrillSergeantConfig:
    """Create a strict DrillSergeantConfig for testing."""
    return DrillSergeantConfig(
        mode="strict",
        persona="drill_sergeant",
        budgets={"warn": 10, "error": 0},
        thresholds={"bis_threshold_warn": 90, "bis_threshold_fail": 70},
        enabled_rules={"aaa_comments", "private_access", "static_clones"},
        suppressed_rules=set(),
        fail_on_how=True,
        verbose=True,
    )


@pytest.fixture
def advisory_config() -> DrillSergeantConfig:
    """Create an advisory DrillSergeantConfig for testing."""
    return DrillSergeantConfig(
        mode="advisory",
        persona="snoop_dogg",
        budgets={"warn": 25, "error": 5},
        thresholds={"bis_threshold_warn": 80, "bis_threshold_fail": 60},
        enabled_rules={"aaa_comments", "private_access"},
        suppressed_rules={"private_access"},
        fail_on_how=False,
        verbose=False,
    )


@pytest.fixture
def mock_pytest_config() -> MagicMock:
    """Create a mock pytest config for testing."""
    mock_config = MagicMock()
    mock_config.option = MagicMock()
    mock_config.option.ds_mode = "advisory"
    mock_config.option.ds_persona = "drill_sergeant"
    mock_config.option.ds_verbose = False
    mock_config.option.ds_quiet = False
    mock_config.option.ds_fail_on_how = False
    return mock_config


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory with configuration files."""
    project_root = tmp_path

    # Create pyproject.toml
    pyproject_content = """
[tool.pytest-drill-sergeant]
mode = "advisory"
persona = "drill_sergeant"
budgets = { warn = 25, error = 5 }
thresholds = { bis_threshold_warn = 80, bis_threshold_fail = 60 }
enabled_rules = ["aaa_comments", "private_access"]
mock_allowlist = ["requests.*", "boto3.*"]
"""
    (project_root / "pyproject.toml").write_text(pyproject_content)

    # Create pytest.ini
    pytest_ini_content = """
[tool:pytest-drill-sergeant]
mode = quality-gate
persona = snoop_dogg
verbose = true
budgets = warn=20,error=10
enabled_rules = aaa_comments,static_clones
"""
    (project_root / "pytest.ini").write_text(pytest_ini_content)

    return Path(project_root)


@pytest.fixture
def mock_import() -> Generator[MagicMock, None, None]:
    """Mock the import function for testing SUT package validation."""
    with patch("builtins.__import__") as mock_import_func:
        yield mock_import_func


@pytest.fixture
def mock_path_exists() -> Generator[MagicMock, None, None]:
    """Mock pathlib.Path.exists for testing file path validation."""
    with patch("pathlib.Path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_path_is_dir() -> Generator[MagicMock, None, None]:
    """Mock pathlib.Path.is_dir for testing directory validation."""
    with patch("pathlib.Path.is_dir") as mock_is_dir:
        yield mock_is_dir


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest for drill sergeant tests."""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker for tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker for tests in integration/ directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add slow marker for tests that take longer to run
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)
