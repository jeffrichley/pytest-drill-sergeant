"""Unit tests for explicit AAA comment grammar behavior."""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import (
    AAAValidator,
    _has_descriptive_comment,
    _parse_aaa_comment,
)


@pytest.mark.unit
class TestAAACommentGrammar:
    """Test explicit grammar parsing for AAA comments."""

    def test_parse_accepts_case_insensitive_keyword(self) -> None:
        """# Arrange - Lowercase AAA comment line
        # Act - Parse AAA comment
        # Assert - Keyword and description are extracted
        """
        # Arrange - Lowercase keyword with valid description
        line = "# arrange - set up user fixture"

        # Act - Parse line with AAA grammar
        parsed = _parse_aaa_comment(line)

        # Assert - Parsed keyword and description are present
        assert parsed is not None
        assert parsed[0] == "arrange"
        assert parsed[1] == "set up user fixture"

    def test_parse_accepts_flexible_spacing_around_dash(self) -> None:
        """# Arrange - AAA comment with tight spacing
        # Act - Parse AAA comment
        # Assert - Grammar still parses keyword and description
        """
        # Arrange - Mixed spacing around keyword and dash
        line = "#   Act- run command"

        # Act - Parse with flexible spacing grammar
        parsed = _parse_aaa_comment(line)

        # Assert - Parsed successfully
        assert parsed == ("Act", "run command")

    def test_parse_rejects_missing_hash_prefix(self) -> None:
        """# Arrange - AAA-like line without hash marker
        # Act - Parse AAA comment
        # Assert - Returns None for invalid grammar
        """
        # Arrange - Missing comment marker
        line = "Arrange - set up"

        # Act - Parse invalid line
        parsed = _parse_aaa_comment(line)

        # Assert - Invalid AAA grammar is rejected
        assert parsed is None

    def test_has_descriptive_comment_rejects_blank_description(self) -> None:
        """# Arrange - AAA comment with blank description
        # Act - Validate descriptive comment length
        # Assert - Returns False
        """
        # Arrange - Description is blank after trim
        line = "# Assert -     "

        # Act - Validate descriptive content
        is_descriptive = _has_descriptive_comment(line, min_length=3)

        # Assert - Blank description is not descriptive
        assert is_descriptive is False

    def test_validator_detects_sections_with_lowercase_keywords(self) -> None:
        """# Arrange - Source lines with lowercase AAA comments
        # Act - Validate AAA sections
        # Assert - All sections are detected
        """
        # Arrange - Lowercase comments should still map to AAA sections
        validator = AAAValidator()
        config = DrillSergeantConfig()
        source_lines = [
            "# arrange - setup context",
            "# act - execute function",
            "# assert - compare output",
        ]

        # Act - Check AAA status from source lines
        status = validator._check_aaa_sections(source_lines, "test_case", config)

        # Assert - Lowercase keywords are recognized
        assert status.arrange_found is True
        assert status.act_found is True
        assert status.assert_found is True
        assert status.issues == []
