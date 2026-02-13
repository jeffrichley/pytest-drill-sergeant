"""AAA (Arrange-Act-Assert) structure validation for pytest-drill-sergeant."""

import inspect
import re
import warnings

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import AAAStatus, ValidationIssue

# Default AAA synonyms for flexible recognition
DEFAULT_AAA_SYNONYMS = {
    "arrange": [
        "Setup",
        "Given",
        "Prepare",
        "Initialize",
        "Configure",
        "Create",
        "Build",
    ],
    "act": ["Call", "Execute", "Run", "Invoke", "Perform", "Trigger", "When"],
    "assert": ["Verify", "Check", "Expect", "Validate", "Confirm", "Ensure", "Then"],
}

AAA_COMMENT_PATTERN = re.compile(
    r"^\s*#\s*(?P<keyword>[A-Za-z][\w ]*?)\s*-\s*(?P<description>.+?)\s*$"
)
SECTION_DESCRIPTIONS = {
    "arrange": "set up",
    "act": "action is being performed",
    "assert": "is being verified",
}
SECTION_ORDER = {"arrange": 0, "act": 1, "assert": 2}


class AAAValidator:
    """Validator for AAA (Arrange-Act-Assert) structure enforcement."""

    def validate(
        self, item: pytest.Item, config: DrillSergeantConfig
    ) -> list[ValidationIssue]:
        """Validate AAA structure and return issues (don't fail immediately)."""
        issues = []

        try:
            source_lines = inspect.getsource(item.function).split("\n")  # type: ignore[attr-defined]
            aaa_status = self._check_aaa_sections(source_lines, item.name, config)
            issues.extend(aaa_status.issues)

            # Check for missing sections and add appropriate issues
            self._add_missing_section_issues(aaa_status, item.name, issues, config)

        except OSError:
            # Can't get source (e.g., dynamic tests), skip AAA validation
            pass

        if issues and config.aaa_severity == "warn":
            for issue in issues:
                warnings.warn(pytest.PytestWarning(issue.message), stacklevel=2)
            return []

        return issues

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if AAA validation is enabled."""
        return config.enforce_aaa and config.aaa_severity != "off"

    def _check_aaa_sections(
        self, source_lines: list[str], test_name: str, config: DrillSergeantConfig
    ) -> AAAStatus:
        """Check for AAA sections in source lines and validate descriptive comments."""
        status = AAAStatus()
        keyword_lookup = _build_aaa_keyword_lookup(config)

        for source_line in source_lines:
            line = source_line.strip()

            # Only check comment lines
            if not line.startswith("#"):
                continue

            parsed = _parse_aaa_comment(line)
            if parsed is None:
                continue

            keyword, _description = parsed
            section_name = keyword_lookup.get(keyword.lower())
            if section_name is None:
                continue

            setattr(status, f"{section_name}_found", True)
            status.section_sequence.append(section_name)
            validation_context = (line, test_name, section_name)
            self._check_descriptive_comment(status, validation_context, config)

        return status

    def _check_descriptive_comment(
        self,
        status: AAAStatus,
        validation_context: tuple[str, str, str],
        config: DrillSergeantConfig,
    ) -> None:
        """Check if a comment line has descriptive content."""
        line, test_name, section_name = validation_context
        if not _has_descriptive_comment(line, config.min_description_length):
            description = SECTION_DESCRIPTIONS[section_name]
            section_label = section_name.title()
            status.issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' has '{section_label}' but missing descriptive comment",
                    suggestion=f"Add '# {section_label} - description of what {description}' with at least {config.min_description_length} characters",
                )
            )

    def _add_missing_section_issues(
        self,
        aaa_status: AAAStatus,
        test_name: str,
        issues: list[ValidationIssue],
        config: DrillSergeantConfig,
    ) -> None:
        """Add issues for missing AAA sections."""
        if not aaa_status.arrange_found:
            issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' is missing 'Arrange' section",
                    suggestion="Add '# Arrange - description of what is being set up' comment before test setup",
                )
            )

        if not aaa_status.act_found:
            issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' is missing 'Act' section",
                    suggestion="Add '# Act - description of what action is being performed' comment before test action",
                )
            )

        if not aaa_status.assert_found:
            issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' is missing 'Assert' section",
                    suggestion="Add '# Assert - description of what is being verified' comment before test verification",
                )
            )

        if config.aaa_mode.lower() == "strict":
            self._add_strict_mode_issues(aaa_status, test_name, issues)

    def _add_strict_mode_issues(
        self, aaa_status: AAAStatus, test_name: str, issues: list[ValidationIssue]
    ) -> None:
        """Add strict-mode issues for order and duplicate AAA sections."""
        if _has_duplicate_sections(aaa_status.section_sequence):
            issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' has duplicate AAA section comments",
                    suggestion="In strict mode, use at most one section header for each of Arrange, Act, and Assert",
                )
            )

        if _is_out_of_order(aaa_status.section_sequence):
            issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' has AAA sections out of order",
                    suggestion="In strict mode, section headers must appear in Arrange -> Act -> Assert order",
                )
            )


def _build_aaa_keyword_lists(config: DrillSergeantConfig) -> dict[str, list[str]]:
    """Build complete keyword lists for AAA detection including synonyms."""
    keywords = {"arrange": ["Arrange"], "act": ["Act"], "assert": ["Assert"]}

    # Add synonyms if enabled
    if config.aaa_synonyms_enabled:
        # Add built-in synonyms
        if config.aaa_builtin_synonyms:
            keywords["arrange"].extend(DEFAULT_AAA_SYNONYMS["arrange"])
            keywords["act"].extend(DEFAULT_AAA_SYNONYMS["act"])
            keywords["assert"].extend(DEFAULT_AAA_SYNONYMS["assert"])

        # Add custom synonyms
        keywords["arrange"].extend(config.aaa_arrange_synonyms)
        keywords["act"].extend(config.aaa_act_synonyms)
        keywords["assert"].extend(config.aaa_assert_synonyms)

    return keywords


def _build_aaa_keyword_lookup(config: DrillSergeantConfig) -> dict[str, str]:
    """Build a case-insensitive keyword lookup to AAA section names."""
    keywords = _build_aaa_keyword_lists(config)
    lookup: dict[str, str] = {}
    for section_name, section_keywords in keywords.items():
        for keyword in section_keywords:
            normalized = keyword.strip().lower()
            if normalized and normalized not in lookup:
                lookup[normalized] = section_name
    return lookup


def _parse_aaa_comment(line: str) -> tuple[str, str] | None:
    """Parse comment line into (keyword, description) using AAA grammar."""
    match = AAA_COMMENT_PATTERN.match(line)
    if match is None:
        return None

    keyword = match.group("keyword").strip()
    description = match.group("description").strip()
    if not keyword:
        return None
    return keyword, description


def _has_duplicate_sections(section_sequence: list[str]) -> bool:
    """Check if AAA section sequence contains duplicate section names."""
    seen: set[str] = set()
    for section in section_sequence:
        if section in seen:
            return True
        seen.add(section)
    return False


def _is_out_of_order(section_sequence: list[str]) -> bool:
    """Check if AAA sections violate Arrange -> Act -> Assert order."""
    max_order_seen = -1
    for section in section_sequence:
        section_order = SECTION_ORDER.get(section, -1)
        if section_order < max_order_seen:
            return True
        max_order_seen = max(max_order_seen, section_order)
    return False


def _validate_aaa_structure(
    item: pytest.Item, config: DrillSergeantConfig
) -> list[ValidationIssue]:
    """Validate AAA structure and return issues (don't fail immediately)."""
    validator = AAAValidator()
    return validator.validate(item, config)


def _has_descriptive_comment(line: str, min_length: int = 3) -> bool:
    """Check if a comment line has valid AAA grammar and descriptive text."""
    parsed = _parse_aaa_comment(line)
    if parsed is None:
        return False

    _keyword, description = parsed
    return len(description) >= min_length
