"""Rule specification system for pytest-drill-sergeant.

This module defines the stable rule codes (DS###) and metadata for all rules
in the system. It replaces the old name-based rule system with a robust,
versioned approach that enables inline suppressions, per-file ignores, and
long-term stability.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Severity levels for findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class RuleCategory(str, Enum):
    """Categories for organizing rules."""

    TEST_QUALITY = "test_quality"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"


class RuleSpec(BaseModel):
    """Specification for a single rule with stable code and metadata."""

    code: str = Field(description="Stable rule code (e.g., DS201)")
    name: str = Field(description="Human-readable rule name")
    default_level: Severity = Field(description="Default severity level")
    short_desc: str = Field(description="Brief description for CLI output")
    long_desc: str = Field(description="Detailed description for help")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    fixable: bool = Field(
        default=False, description="Whether rule violations can be auto-fixed"
    )
    category: RuleCategory = Field(description="Rule category")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate rule code format."""
        if not v.startswith("DS"):
            raise ValueError("Rule code must start with 'DS'")
        if len(v) != 5:
            raise ValueError("Rule code must be 5 characters (DS###)")
        try:
            int(v[2:])
        except ValueError:
            raise ValueError("Rule code must be DS followed by 3 digits")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags are non-empty strings."""
        for tag in v:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("Tags must be non-empty strings")
        return v


class RuleRegistry:
    """Registry for all rules in the system."""

    _rules: dict[str, RuleSpec] = {}
    _rules_by_name: dict[str, str] = {}  # name -> code mapping

    @classmethod
    def register_rule(cls, rule: RuleSpec) -> None:
        """Register a rule in the registry."""
        cls._rules[rule.code] = rule
        cls._rules_by_name[rule.name] = rule.code

    @classmethod
    def get_rule(cls, identifier: str) -> RuleSpec:
        """Get a rule by code or name.

        Args:
            identifier: Rule code (DS201) or name (duplicate_tests)

        Returns:
            Rule specification

        Raises:
            KeyError: If rule not found
        """
        # Try as code first
        if identifier in cls._rules:
            return cls._rules[identifier]

        # Try as name
        if identifier in cls._rules_by_name:
            code = cls._rules_by_name[identifier]
            return cls._rules[code]

        raise KeyError(f"Rule not found: {identifier}")

    @classmethod
    def get_all_rules(cls) -> list[RuleSpec]:
        """Get all registered rules."""
        return list(cls._rules.values())

    @classmethod
    def get_rules_by_category(cls, category: RuleCategory) -> list[RuleSpec]:
        """Get all rules in a category."""
        return [rule for rule in cls._rules.values() if rule.category == category]

    @classmethod
    def get_rules_by_tag(cls, tag: str) -> list[RuleSpec]:
        """Get all rules with a specific tag."""
        return [rule for rule in cls._rules.values() if tag in rule.tags]

    @classmethod
    def is_valid_rule(cls, identifier: str) -> bool:
        """Check if a rule identifier is valid."""
        return identifier in cls._rules or identifier in cls._rules_by_name


# Define all rules with stable codes
# DS2xx - Test Quality Issues
DUPLICATE_TESTS = RuleSpec(
    code="DS201",
    name="duplicate_tests",
    default_level=Severity.WARNING,
    short_desc="Detect near-duplicate test bodies",
    long_desc="Computes token-similarity between test functions and flags clones above threshold. Helps identify test code duplication that reduces maintainability.",
    tags=["duplication", "quality", "maintainability"],
    fixable=True,
    category=RuleCategory.TEST_QUALITY,
)

FIXTURE_SMELLS = RuleSpec(
    code="DS202",
    name="fixture_smells",
    default_level=Severity.WARNING,
    short_desc="Detect problematic fixture patterns",
    long_desc="Identifies fixtures that are too complex, have side effects, or violate fixture best practices. Helps maintain clean test architecture.",
    tags=["fixtures", "quality", "architecture"],
    fixable=False,
    category=RuleCategory.TEST_QUALITY,
)

HOW_NOT_WHAT = RuleSpec(
    code="DS203",
    name="how_not_what",
    default_level=Severity.WARNING,
    short_desc="Test should verify behavior, not implementation",
    long_desc="Flags tests that verify internal implementation details rather than external behavior. Tests should focus on what the code does, not how it does it.",
    tags=["testing", "quality", "behavior"],
    fixable=False,
    category=RuleCategory.TEST_QUALITY,
)

OVERMOCKING = RuleSpec(
    code="DS204",
    name="overmocking",
    default_level=Severity.WARNING,
    short_desc="Detect excessive use of mocks",
    long_desc="Identifies tests that mock too many dependencies, making tests brittle and less valuable. Suggests using real objects where appropriate.",
    tags=["mocking", "quality", "brittleness"],
    fixable=False,
    category=RuleCategory.TEST_QUALITY,
)

NONDETERMINISM = RuleSpec(
    code="DS205",
    name="nondeterminism",
    default_level=Severity.ERROR,
    short_desc="Detect non-deterministic test behavior",
    long_desc="Flags tests that may produce different results on different runs due to timing, random data, or external dependencies. These tests are unreliable.",
    tags=["reliability", "flaky", "quality"],
    fixable=False,
    category=RuleCategory.TEST_QUALITY,
)

NAMING_HYGIENE = RuleSpec(
    code="DS206",
    name="naming_hygiene",
    default_level=Severity.INFO,
    short_desc="Check test naming conventions",
    long_desc="Validates that test names follow good conventions and clearly describe what is being tested. Poor naming makes tests hard to understand and maintain.",
    tags=["naming", "conventions", "readability"],
    fixable=True,
    category=RuleCategory.TEST_QUALITY,
)

# DS3xx - Code Quality Issues
PRIVATE_ACCESS = RuleSpec(
    code="DS301",
    name="private_access",
    default_level=Severity.WARNING,
    short_desc="Detect access to private members in tests",
    long_desc="Flags tests that access private methods, attributes, or modules. Tests should use public APIs to avoid brittleness when implementation changes.",
    tags=["encapsulation", "quality", "brittleness"],
    fixable=False,
    category=RuleCategory.CODE_QUALITY,
)

AAA_COMMENTS = RuleSpec(
    code="DS302",
    name="aaa_comments",
    default_level=Severity.INFO,
    short_desc="Check for Arrange-Act-Assert pattern in tests",
    long_desc="Validates that tests follow the AAA pattern with clear sections for setup, execution, and verification. Improves test readability and structure.",
    tags=["structure", "readability", "patterns"],
    fixable=True,
    category=RuleCategory.CODE_QUALITY,
)

STATIC_CLONES = RuleSpec(
    code="DS303",
    name="static_clones",
    default_level=Severity.WARNING,
    short_desc="Detect static code duplication",
    long_desc="Identifies duplicate code blocks in test files using static analysis. Helps reduce maintenance burden and improve code quality.",
    tags=["duplication", "quality", "maintainability"],
    fixable=True,
    category=RuleCategory.CODE_QUALITY,
)

FIXTURE_EXTRACT = RuleSpec(
    code="DS304",
    name="fixture_extract",
    default_level=Severity.WARNING,
    short_desc="Suggest fixture extraction opportunities",
    long_desc="Identifies common setup code that could be extracted into fixtures. Helps reduce duplication and improve test organization.",
    tags=["fixtures", "refactoring", "duplication"],
    fixable=True,
    category=RuleCategory.CODE_QUALITY,
)

MOCK_OVERSPECIFICATION = RuleSpec(
    code="DS305",
    name="mock_overspecification",
    default_level=Severity.WARNING,
    short_desc="Detect over-specified mock expectations",
    long_desc="Flags mocks that are too specific about method calls, parameters, or return values. Over-specification makes tests brittle and hard to maintain.",
    tags=["mocking", "brittleness", "quality"],
    fixable=False,
    category=RuleCategory.CODE_QUALITY,
)

STRUCTURAL_EQUALITY = RuleSpec(
    code="DS306",
    name="structural_equality",
    default_level=Severity.WARNING,
    short_desc="Check for proper equality testing",
    long_desc="Validates that tests use appropriate equality assertions and don't rely on object identity when value equality is intended.",
    tags=["assertions", "quality", "correctness"],
    fixable=False,
    category=RuleCategory.CODE_QUALITY,
)


def register_all_rules() -> None:
    """Register all rules in the registry."""
    rules = [
        DUPLICATE_TESTS,
        FIXTURE_SMELLS,
        HOW_NOT_WHAT,
        OVERMOCKING,
        NONDETERMINISM,
        NAMING_HYGIENE,
        PRIVATE_ACCESS,
        AAA_COMMENTS,
        STATIC_CLONES,
        FIXTURE_EXTRACT,
        MOCK_OVERSPECIFICATION,
        STRUCTURAL_EQUALITY,
    ]

    for rule in rules:
        RuleRegistry.register_rule(rule)


# Auto-register all rules when module is imported
register_all_rules()
