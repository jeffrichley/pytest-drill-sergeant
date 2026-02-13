"""Unit tests for layered config precedence and pyproject support."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig


class DummyConfig:
    """Minimal pytest config stub for config loading tests."""

    def __init__(self, rootpath: Path, values: dict[str, object]) -> None:
        """Store root path and a simple getini mapping."""
        self.rootpath = rootpath
        self.inipath = rootpath / "pytest.ini"
        self._values = values

    def getini(self, key: str) -> object | None:
        """Return an ini value from the in-memory mapping."""
        return self._values.get(key)


@pytest.mark.unit
class TestDrillSergeantConfigPrecedence:
    """Test layered precedence: env > pytest > tool.drill_sergeant > defaults."""

    def test_loads_from_tool_drill_sergeant_when_pytest_missing(
        self, tmp_path: Path
    ) -> None:
        """# Arrange - Write [tool.drill_sergeant] config and empty pytest layer
        # Act - Build DrillSergeantConfig from dummy pytest config
        # Assert - Values resolve from [tool.drill_sergeant]
        """
        # Arrange - Populate pyproject.toml with drill-sergeant settings
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.drill_sergeant]
enabled = true
enforce_markers = false
enforce_aaa = false
enforce_file_length = false
auto_detect_markers = false
min_description_length = 11
max_file_length = 777
aaa_synonyms_enabled = true
aaa_builtin_synonyms = false
aaa_arrange_synonyms = ["Given", "Setup"]
aaa_act_synonyms = ["When", "Execute"]
aaa_assert_synonyms = ["Then", "Verify"]

[tool.drill_sergeant.marker_mappings]
contract = "api"
smoke = "integration"
""".strip(),
            encoding="utf-8",
        )
        config = DummyConfig(tmp_path, {})

        # Act - Resolve layered configuration
        resolved = DrillSergeantConfig.from_pytest_config(config)  # type: ignore[arg-type]

        # Assert - Tool values are used when pytest layer is empty
        assert resolved.enabled is True
        assert resolved.enforce_markers is False
        assert resolved.enforce_aaa is False
        assert resolved.enforce_file_length is False
        assert resolved.auto_detect_markers is False
        assert resolved.min_description_length == 11
        assert resolved.max_file_length == 777
        assert resolved.aaa_synonyms_enabled is True
        assert resolved.aaa_builtin_synonyms is False
        assert resolved.aaa_arrange_synonyms == ["Given", "Setup"]
        assert resolved.aaa_act_synonyms == ["When", "Execute"]
        assert resolved.aaa_assert_synonyms == ["Then", "Verify"]
        assert resolved.marker_mappings == {"contract": "api", "smoke": "integration"}

    def test_pytest_layer_overrides_tool_layer(self, tmp_path: Path) -> None:
        """# Arrange - Configure conflicting values in tool and pytest layers
        # Act - Build DrillSergeantConfig from dummy pytest config
        # Assert - Pytest values override tool values
        """
        # Arrange - Tool says false/low values while pytest says true/higher values
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.drill_sergeant]
enabled = false
enforce_markers = false
min_description_length = 4
max_file_length = 100
""".strip(),
            encoding="utf-8",
        )
        config = DummyConfig(
            tmp_path,
            {
                "drill_sergeant_enabled": "true",
                "drill_sergeant_enforce_markers": "true",
                "drill_sergeant_min_description_length": "8",
                "drill_sergeant_max_file_length": "600",
            },
        )

        # Act - Resolve layered configuration
        resolved = DrillSergeantConfig.from_pytest_config(config)  # type: ignore[arg-type]

        # Assert - Pytest layer wins over tool layer
        assert resolved.enabled is True
        assert resolved.enforce_markers is True
        assert resolved.min_description_length == 8
        assert resolved.max_file_length == 600

    def test_environment_layer_overrides_all_other_layers(self, tmp_path: Path) -> None:
        """# Arrange - Configure values in tool and pytest, then set env overrides
        # Act - Build DrillSergeantConfig under env overrides
        # Assert - Environment variables have highest priority
        """
        # Arrange - Configure lower-priority layers
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.drill_sergeant]
enabled = true
enforce_markers = true
min_description_length = 5
max_file_length = 500
""".strip(),
            encoding="utf-8",
        )
        config = DummyConfig(
            tmp_path,
            {
                "drill_sergeant_enabled": "true",
                "drill_sergeant_enforce_markers": "true",
                "drill_sergeant_min_description_length": "10",
                "drill_sergeant_max_file_length": "1000",
            },
        )

        # Act - Apply environment overrides and resolve config
        with patch.dict(
            os.environ,
            {
                "DRILL_SERGEANT_ENABLED": "true",
                "DRILL_SERGEANT_ENFORCE_MARKERS": "false",
                "DRILL_SERGEANT_MIN_DESCRIPTION_LENGTH": "22",
                "DRILL_SERGEANT_MAX_FILE_LENGTH": "2222",
            },
        ):
            resolved = DrillSergeantConfig.from_pytest_config(config)  # type: ignore[arg-type]

        # Assert - Environment layer wins
        assert resolved.enabled is True
        assert resolved.enforce_markers is False
        assert resolved.min_description_length == 22
        assert resolved.max_file_length == 2222

    def test_marker_mapping_layers_merge_by_key(self, tmp_path: Path) -> None:
        """# Arrange - Define marker mappings at tool, pytest, and env layers
        # Act - Resolve DrillSergeantConfig marker mappings
        # Assert - Layered merge uses tool base, pytest overrides, env final overrides
        """
        # Arrange - Build base and override mappings across layers
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.drill_sergeant.marker_mappings]
contract = "api"
smoke = "integration"
""".strip(),
            encoding="utf-8",
        )
        config = DummyConfig(
            tmp_path,
            {"drill_sergeant_marker_mappings": "contract=service,load=performance"},
        )

        # Act - Apply top-layer env mappings
        with patch.dict(
            os.environ,
            {"DRILL_SERGEANT_MARKER_MAPPINGS": "contract=edge,bench=performance"},
        ):
            resolved = DrillSergeantConfig.from_pytest_config(config)  # type: ignore[arg-type]

        # Assert - Final map reflects key-level precedence and merge
        assert resolved.marker_mappings == {
            "contract": "edge",
            "smoke": "integration",
            "load": "performance",
            "bench": "performance",
        }
