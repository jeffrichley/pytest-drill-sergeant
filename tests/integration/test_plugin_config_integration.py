"""Integration tests for plugin config registration and debug behavior."""

from unittest.mock import patch

import pytest
from _pytest.pytester import Pytester


@pytest.mark.integration
class TestPluginConfigIntegration:
    """Test plugin configuration hooks in isolated pytest runs."""

    def test_plugin_registers_custom_ini_options(self, pytester: Pytester) -> None:
        """# Arrange - Pytest config with drill-sergeant ini options
        # Act - Run pytest treating config warnings as errors
        # Assert - Drill-sergeant options are recognized and run succeeds
        """
        # Arrange - Add drill-sergeant ini options that must be registered by plugin
        pytester.makefile(
            ".ini",
            pytest="""
[pytest]
drill_sergeant_enabled = false
drill_sergeant_enforce_markers = false
drill_sergeant_enforce_aaa = false
drill_sergeant_enforce_file_length = false
drill_sergeant_auto_detect_markers = false
drill_sergeant_min_description_length = 3
drill_sergeant_max_file_length = 350
drill_sergeant_marker_mappings = contract=api,smoke=integration
drill_sergeant_aaa_synonyms_enabled = false
drill_sergeant_aaa_builtin_synonyms = true
""",
        )
        pytester.makepyfile(
            test_ini_options="""
            def test_ini_options() -> None:
                assert True
""",
        )

        # Act - Fail hard if any PytestConfigWarning appears
        result = pytester.runpytest(
            "-p",
            "drill_sergeant",
            "-W",
            "error::pytest.PytestConfigWarning",
        )

        # Assert - Unknown ini option warnings are not raised
        assert result.ret == 0

    def test_disabled_mode_skips_enforcement(self, pytester: Pytester) -> None:
        """# Arrange - Drill sergeant disabled with intentionally bad test
        # Act - Run pytest with plugin loaded
        # Assert - Test still passes because enforcement is disabled
        """
        # Arrange - Disable plugin and create a test that would otherwise fail checks
        pytester.makefile(
            ".ini",
            pytest="""
[pytest]
drill_sergeant_enabled = false
""",
        )
        pytester.makepyfile(
            test_disabled_mode="""
            def test_no_marker_no_aaa():
                value = 2
                assert value == 2
""",
        )

        # Act - Run with drill-sergeant plugin enabled in pytest
        result = pytester.runpytest("-p", "drill_sergeant")

        # Assert - Enforcement is bypassed when disabled
        assert result.ret == 0

    def test_debug_config_emits_effective_config_once(self, pytester: Pytester) -> None:
        """# Arrange - Enable debug config output
        # Act - Run pytest with drill-sergeant plugin
        # Assert - Effective config line is emitted
        """
        # Arrange - Minimal passing test and debug env var
        pytester.makefile(
            ".ini",
            pytest="""
[pytest]
drill_sergeant_enabled = false
""",
        )
        pytester.makepyfile(
            test_debug_config="""
            def test_debug_config() -> None:
                assert True
""",
        )

        # Act - Enable one-time config debug output
        with patch.dict("os.environ", {"DRILL_SERGEANT_DEBUG_CONFIG": "true"}):
            result = pytester.runpytest("-p", "drill_sergeant")

        # Assert - Debug output includes effective config line
        assert result.ret == 0
        result.stdout.fnmatch_lines(["*drill-sergeant effective config:*"])

    def test_marker_discovery_works_with_pytest_ini_markers(
        self, pytester: Pytester
    ) -> None:
        """# Arrange - Pytest ini declares markers and DS marker enforcement
        # Act - Run a markerless test under tests/unit with auto-detection
        # Assert - Marker is discovered from pytest ini and test passes
        """
        # Arrange - Configure marker enforcement with marker declaration in pytest.ini
        pytester.makefile(
            ".ini",
            pytest="""
[pytest]
markers =
    unit: Unit tests
drill_sergeant_enabled = true
drill_sergeant_enforce_markers = true
drill_sergeant_auto_detect_markers = true
drill_sergeant_enforce_aaa = false
drill_sergeant_enforce_file_length = false
""",
        )
        pytester.mkdir("tests")
        pytester.mkdir("tests/unit")
        unit_test = pytester.path / "tests" / "unit" / "test_ini_marker_discovery.py"
        unit_test.write_text(
            """
def test_ini_marker_discovery():
    value = 1
    assert value == 1
""".strip(),
            encoding="utf-8",
        )

        # Act - Run drill-sergeant enabled test session
        result = pytester.runpytest("-p", "drill_sergeant")

        # Assert - Marker discovery from pytest.ini works
        assert result.ret == 0

    def test_marker_discovery_works_with_pyproject_toml_markers(
        self, pytester: Pytester
    ) -> None:
        """# Arrange - Pyproject TOML declares pytest markers and DS options
        # Act - Run markerless test under tests/unit with auto-detection
        # Assert - Marker is discovered from TOML pytest config and test passes
        """
        # Arrange - Configure pytest and drill-sergeant via pyproject TOML
        pytester.makefile(
            ".toml",
            pyproject="""
[tool.pytest.ini_options]
markers = ["unit: Unit tests"]
drill_sergeant_enabled = true
drill_sergeant_enforce_markers = true
drill_sergeant_auto_detect_markers = true
drill_sergeant_enforce_aaa = false
drill_sergeant_enforce_file_length = false
""",
        )
        pytester.mkdir("tests")
        pytester.mkdir("tests/unit")
        unit_test = pytester.path / "tests" / "unit" / "test_toml_marker_discovery.py"
        unit_test.write_text(
            """
def test_toml_marker_discovery():
    value = 2
    assert value == 2
""".strip(),
            encoding="utf-8",
        )

        # Act - Run drill-sergeant enabled test session
        result = pytester.runpytest("-p", "drill_sergeant")

        # Assert - Marker discovery from pyproject TOML works
        assert result.ret == 0
