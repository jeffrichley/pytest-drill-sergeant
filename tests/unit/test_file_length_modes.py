"""Unit tests for file length validator modes and exemptions."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.file_length import FileLengthValidator


def _make_item(file_path: Path, rootpath: Path) -> Mock:
    """Create a minimal pytest item mock for file length checks."""
    item = Mock()
    item.fspath = str(file_path)
    item.config = Mock()
    item.config.rootpath = rootpath
    return item


@pytest.mark.unit
class TestFileLengthModes:
    """Test configurable file length behavior."""

    def test_error_mode_reports_issue_when_file_exceeds_limit(self, tmp_path: Path) -> None:
        """# Arrange - Long test file and error mode
        # Act - Run file length validator
        # Assert - Returns one file_length issue
        """
        # Arrange - Create file with 6 lines and limit 5
        test_file = tmp_path / "tests" / "unit" / "test_long.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("\n".join(["line"] * 6), encoding="utf-8")
        item = _make_item(test_file, tmp_path)
        config = DrillSergeantConfig(max_file_length=5, file_length_mode="error")
        validator = FileLengthValidator()

        # Act - Validate file length
        issues = validator.validate(item, config)

        # Assert - File length issue is reported
        assert len(issues) == 1
        assert issues[0].issue_type == "file_length"

    def test_warn_mode_emits_warning_and_does_not_return_issue(
        self, tmp_path: Path
    ) -> None:
        """# Arrange - Long test file and warn mode
        # Act - Run file length validator
        # Assert - Emits warning and returns no issues
        """
        # Arrange - Create file with 6 lines and limit 5
        test_file = tmp_path / "tests" / "unit" / "test_long_warn.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("\n".join(["line"] * 6), encoding="utf-8")
        item = _make_item(test_file, tmp_path)
        config = DrillSergeantConfig(max_file_length=5, file_length_mode="warn")
        validator = FileLengthValidator()

        # Act/Assert - Warning mode should warn but not return issues
        with pytest.warns(pytest.PytestWarning):
            issues = validator.validate(item, config)
        assert issues == []

    def test_off_mode_disables_file_length_validation(self, tmp_path: Path) -> None:
        """# Arrange - Long test file and off mode
        # Act - Run file length validator
        # Assert - Returns no issues and validator is disabled
        """
        # Arrange - Create file with 6 lines and limit 5
        test_file = tmp_path / "tests" / "unit" / "test_long_off.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("\n".join(["line"] * 6), encoding="utf-8")
        item = _make_item(test_file, tmp_path)
        config = DrillSergeantConfig(max_file_length=5, file_length_mode="off")
        validator = FileLengthValidator()

        # Act - Validate file length
        issues = validator.validate(item, config)

        # Assert - Mode off disables validator behavior
        assert validator.is_enabled(config) is False
        assert issues == []

    def test_path_exclusion_skips_file_length_check(self, tmp_path: Path) -> None:
        """# Arrange - Long file matching exclusion glob
        # Act - Run file length validator
        # Assert - File is ignored and no issue is returned
        """
        # Arrange - Excluded path pattern should skip validation
        test_file = tmp_path / "tests" / "legacy" / "test_big.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("\n".join(["line"] * 20), encoding="utf-8")
        item = _make_item(test_file, tmp_path)
        config = DrillSergeantConfig(
            max_file_length=5,
            file_length_mode="error",
            file_length_exclude=["tests/legacy/*"],
        )
        validator = FileLengthValidator()

        # Act - Validate file length
        issues = validator.validate(item, config)

        # Assert - Excluded path bypasses validation
        assert issues == []

    def test_inline_ignore_pragma_skips_file_length_check(self, tmp_path: Path) -> None:
        """# Arrange - Long file with inline ignore pragma
        # Act - Run file length validator
        # Assert - Inline pragma bypasses length violation
        """
        # Arrange - Inline pragma token should skip validation
        test_file = tmp_path / "tests" / "unit" / "test_pragma.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text(
            "\n".join(
                [
                    "# drill-sergeant: file-length ignore",
                    *["line" for _ in range(20)],
                ]
            ),
            encoding="utf-8",
        )
        item = _make_item(test_file, tmp_path)
        config = DrillSergeantConfig(max_file_length=5, file_length_mode="error")
        validator = FileLengthValidator()

        # Act - Validate file length
        issues = validator.validate(item, config)

        # Assert - Inline pragma suppresses file length issue
        assert issues == []
