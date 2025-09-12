"""Unit tests for AAA synonym recognition functionality."""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import AAAValidator, _build_aaa_keyword_lists


@pytest.mark.unit
class TestAAASynonymRecognition:
    """Test AAA synonym recognition functionality."""

    def test_build_aaa_keyword_lists_disabled_by_default(self) -> None:
        """# Arrange - Default configuration with synonyms disabled
        # Act - Build AAA keyword lists
        # Assert - Only original keywords are present
        """
        # Arrange - Default configuration with synonyms disabled
        config = DrillSergeantConfig()

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Only original keywords should be present
        assert keywords["arrange"] == ["Arrange"]
        assert keywords["act"] == ["Act"]
        assert keywords["assert"] == ["Assert"]

    def test_build_aaa_keyword_lists_with_builtin_synonyms(self) -> None:
        """# Arrange - Configuration with built-in synonyms enabled
        # Act - Build AAA keyword lists
        # Assert - Original and built-in synonyms are included
        """
        # Arrange - Configuration with built-in synonyms enabled
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True, aaa_builtin_synonyms=True
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + built-in synonyms
        assert "Arrange" in keywords["arrange"]
        assert "Setup" in keywords["arrange"]
        assert "Given" in keywords["arrange"]

        assert "Act" in keywords["act"]
        assert "Call" in keywords["act"]
        assert "When" in keywords["act"]

        assert "Assert" in keywords["assert"]
        assert "Verify" in keywords["assert"]
        assert "Then" in keywords["assert"]

    def test_build_aaa_keyword_lists_with_custom_synonyms(self) -> None:
        """# Arrange - Configuration with custom synonyms and built-ins disabled
        # Act - Build AAA keyword lists
        # Assert - Only original and custom synonyms are included
        """
        # Arrange - Configuration with custom synonyms and built-ins disabled
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=False,  # Disable built-ins
            aaa_arrange_synonyms=["Background", "Precondition"],
            aaa_act_synonyms=["Execute", "Trigger"],
            aaa_assert_synonyms=["Expect", "Outcome"],
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + custom only (no built-ins)
        assert keywords["arrange"] == ["Arrange", "Background", "Precondition"]
        assert keywords["act"] == ["Act", "Execute", "Trigger"]
        assert keywords["assert"] == ["Assert", "Expect", "Outcome"]

    def test_build_aaa_keyword_lists_with_builtin_and_custom(self) -> None:
        """# Arrange - Configuration with both built-in and custom synonyms
        # Act - Build AAA keyword lists
        # Assert - All synonyms are included together
        """
        # Arrange - Configuration with both built-in and custom synonyms
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=True,
            aaa_arrange_synonyms=["Background"],
            aaa_act_synonyms=["Execute"],
            aaa_assert_synonyms=["Expect"],
        )

        # Act - Build AAA keyword lists
        keywords = _build_aaa_keyword_lists(config)

        # Assert - Should include original + built-ins + custom
        assert "Arrange" in keywords["arrange"]
        assert "Setup" in keywords["arrange"]  # Built-in
        assert "Background" in keywords["arrange"]  # Custom

        assert "Act" in keywords["act"]
        assert "Call" in keywords["act"]  # Built-in
        assert "Execute" in keywords["act"]  # Custom

    def test_synonym_detection_in_comments(self) -> None:
        """# Arrange - Configuration with synonyms enabled and validator
        # Act - Check AAA sections with built-in synonyms
        # Assert - Synonyms are properly detected
        """
        # Arrange - Configuration with synonyms enabled and validator
        config = DrillSergeantConfig(aaa_synonyms_enabled=True)
        validator = AAAValidator()

        # Act - Test built-in synonyms
        status = validator._check_aaa_sections(
            ["# Setup - test data"], "test_func", config
        )

        # Assert - Synonyms are properly detected
        assert status.arrange_found is True

        status = validator._check_aaa_sections(
            ["# Call - the authentication method"], "test_func", config
        )
        assert status.act_found is True

        status = validator._check_aaa_sections(
            ["# Verify - the result is correct"], "test_func", config
        )
        assert status.assert_found is True

    def test_custom_synonym_detection(self) -> None:
        """# Arrange - Configuration with custom BDD-style synonyms
        # Act - Check AAA sections with custom synonyms
        # Assert - Custom synonyms are properly detected
        """
        # Arrange - Configuration with custom BDD-style synonyms
        config = DrillSergeantConfig(
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=False,
            aaa_arrange_synonyms=["Given"],
            aaa_act_synonyms=["When"],
            aaa_assert_synonyms=["Then"],
        )
        validator = AAAValidator()

        # Act - Test BDD-style synonyms
        status = validator._check_aaa_sections(
            ["# Given - a valid user account"], "test_func", config
        )

        # Assert - Custom synonyms are properly detected
        assert status.arrange_found is True

        status = validator._check_aaa_sections(
            ["# When - logging in with credentials"], "test_func", config
        )
        assert status.act_found is True

        status = validator._check_aaa_sections(
            ["# Then - authentication should succeed"], "test_func", config
        )
        assert status.assert_found is True

    def test_synonym_disabled_detection(self) -> None:
        """# Arrange - Configuration with synonyms disabled
        # Act - Check AAA sections with synonym keywords
        # Assert - Synonyms are not detected but original keywords work
        """
        # Arrange - Configuration with synonyms disabled
        config = DrillSergeantConfig(aaa_synonyms_enabled=False)
        validator = AAAValidator()

        # Act - These should NOT be detected when synonyms are disabled
        status = validator._check_aaa_sections(
            ["# Setup - test data"], "test_func", config
        )

        # Assert - Synonyms are not detected but original keywords work
        assert status.arrange_found is False

        status = validator._check_aaa_sections(
            ["# Call - the method"], "test_func", config
        )
        assert status.act_found is False

        status = validator._check_aaa_sections(
            ["# Verify - the result"], "test_func", config
        )
        assert status.assert_found is False

        # But original keywords should still work
        status = validator._check_aaa_sections(
            ["# Arrange - test data"], "test_func", config
        )
        assert status.arrange_found is True
