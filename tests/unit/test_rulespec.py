"""Tests for the rule specification system."""

import pytest

from pytest_drill_sergeant.core.rulespec import (
    RuleRegistry,
    RuleSpec,
    Severity,
    RuleCategory,
    DUPLICATE_TESTS,
    PRIVATE_ACCESS,
)


class TestRuleSpec:
    """Test the RuleSpec model."""

    def test_rule_spec_creation(self):
        """Test creating a rule specification."""
        rule = RuleSpec(
            code="DS999",
            name="test_rule",
            default_level=Severity.WARNING,
            short_desc="Test rule",
            long_desc="This is a test rule for testing purposes",
            tags=["test", "quality"],
            fixable=True,
            category=RuleCategory.TEST_QUALITY
        )
        
        assert rule.code == "DS999"
        assert rule.name == "test_rule"
        assert rule.default_level == Severity.WARNING
        assert rule.fixable is True
        assert "test" in rule.tags

    def test_rule_spec_validation(self):
        """Test rule specification validation."""
        # Valid code
        rule = RuleSpec(
            code="DS201",
            name="test",
            default_level=Severity.WARNING,
            short_desc="Test",
            long_desc="Test",
            category=RuleCategory.TEST_QUALITY
        )
        assert rule.code == "DS201"
        
        # Invalid codes should raise validation error
        with pytest.raises(ValueError, match="Rule code must start with 'DS'"):
            RuleSpec(
                code="INVALID",
                name="test",
                default_level=Severity.WARNING,
                short_desc="Test",
                long_desc="Test",
                category=RuleCategory.TEST_QUALITY
            )
        
        with pytest.raises(ValueError, match="Rule code must be 5 characters"):
            RuleSpec(
                code="DS20",
                name="test",
                default_level=Severity.WARNING,
                short_desc="Test",
                long_desc="Test",
                category=RuleCategory.TEST_QUALITY
            )


class TestRuleRegistry:
    """Test the RuleRegistry functionality."""

    def test_rule_registration(self):
        """Test that rules are automatically registered."""
        # Check that our predefined rules are registered
        assert RuleRegistry.is_valid_rule("DS201")
        assert RuleRegistry.is_valid_rule("duplicate_tests")
        assert RuleRegistry.is_valid_rule("DS301")
        assert RuleRegistry.is_valid_rule("private_access")
        
        # Invalid rules should not be found
        assert not RuleRegistry.is_valid_rule("DS999")
        assert not RuleRegistry.is_valid_rule("invalid_rule")

    def test_get_rule_by_code(self):
        """Test getting rules by code."""
        rule = RuleRegistry.get_rule("DS201")
        assert rule.code == "DS201"
        assert rule.name == "duplicate_tests"
        assert rule.default_level == Severity.WARNING

    def test_get_rule_by_name(self):
        """Test getting rules by name."""
        rule = RuleRegistry.get_rule("duplicate_tests")
        assert rule.code == "DS201"
        assert rule.name == "duplicate_tests"

    def test_get_rule_not_found(self):
        """Test getting non-existent rules."""
        with pytest.raises(KeyError):
            RuleRegistry.get_rule("DS999")
        
        with pytest.raises(KeyError):
            RuleRegistry.get_rule("nonexistent_rule")

    def test_get_all_rules(self):
        """Test getting all registered rules."""
        rules = RuleRegistry.get_all_rules()
        assert len(rules) >= 12  # We have at least 12 predefined rules
        
        # Check that specific rules are included
        codes = [rule.code for rule in rules]
        assert "DS201" in codes
        assert "DS301" in codes

    def test_get_rules_by_category(self):
        """Test getting rules by category."""
        test_quality_rules = RuleRegistry.get_rules_by_category(RuleCategory.TEST_QUALITY)
        assert len(test_quality_rules) >= 6  # We have 6 test quality rules
        
        code_quality_rules = RuleRegistry.get_rules_by_category(RuleCategory.CODE_QUALITY)
        assert len(code_quality_rules) >= 6  # We have 6 code quality rules

    def test_get_rules_by_tag(self):
        """Test getting rules by tag."""
        quality_rules = RuleRegistry.get_rules_by_tag("quality")
        assert len(quality_rules) >= 1
        
        duplication_rules = RuleRegistry.get_rules_by_tag("duplication")
        assert len(duplication_rules) >= 1


class TestPredefinedRules:
    """Test the predefined rule definitions."""

    def test_duplicate_tests_rule(self):
        """Test the duplicate tests rule definition."""
        assert DUPLICATE_TESTS.code == "DS201"
        assert DUPLICATE_TESTS.name == "duplicate_tests"
        assert DUPLICATE_TESTS.default_level == Severity.WARNING
        assert DUPLICATE_TESTS.fixable is True
        assert "duplication" in DUPLICATE_TESTS.tags
        assert DUPLICATE_TESTS.category == RuleCategory.TEST_QUALITY

    def test_private_access_rule(self):
        """Test the private access rule definition."""
        assert PRIVATE_ACCESS.code == "DS301"
        assert PRIVATE_ACCESS.name == "private_access"
        assert PRIVATE_ACCESS.default_level == Severity.WARNING
        assert PRIVATE_ACCESS.fixable is False
        assert "encapsulation" in PRIVATE_ACCESS.tags
        assert PRIVATE_ACCESS.category == RuleCategory.CODE_QUALITY

    def test_rule_consistency(self):
        """Test that predefined rules are consistent."""
        # All rules should have valid codes
        for rule in RuleRegistry.get_all_rules():
            assert rule.code.startswith("DS")
            assert len(rule.code) == 5
            assert rule.code[2:].isdigit()
            
            # All rules should have required fields
            assert rule.name
            assert rule.short_desc
            assert rule.long_desc
            assert rule.category
