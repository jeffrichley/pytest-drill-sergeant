"""AAA (Arrange-Act-Assert) structure validation for pytest-drill-sergeant."""

import inspect

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
            self._add_missing_section_issues(aaa_status, item.name, issues)

        except OSError:
            # Can't get source (e.g., dynamic tests), skip AAA validation
            pass

        return issues

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if AAA validation is enabled."""
        return config.enforce_aaa

    def _check_aaa_sections(
        self, source_lines: list[str], test_name: str, config: DrillSergeantConfig
    ) -> AAAStatus:
        """Check for AAA sections in source lines and validate descriptive comments."""
        status = AAAStatus()
        keywords = _build_aaa_keyword_lists(config)

        for source_line in source_lines:
            line = source_line.strip()

            # Only check comment lines
            if not line.startswith("#"):
                continue

            # Check each AAA section
            self._check_section(
                status,
                line,
                test_name,
                config,
                (keywords["arrange"], "arrange", "set up"),
            )
            self._check_section(
                status,
                line,
                test_name,
                config,
                (keywords["act"], "act", "action is being performed"),
            )
            self._check_section(
                status,
                line,
                test_name,
                config,
                (keywords["assert"], "assert", "is being verified"),
            )

        return status

    def _check_section(
        self,
        status: AAAStatus,
        line: str,
        test_name: str,
        config: DrillSergeantConfig,
        section_info: tuple[list[str], str, str],
    ) -> None:
        """Check if line contains keywords for a specific AAA section."""
        section_keywords, section_name, description = section_info
        if any(keyword in line for keyword in section_keywords):
            # Set the appropriate flag
            setattr(status, f"{section_name}_found", True)
            # Find matched keyword for feedback
            matched_keyword = next(k for k in section_keywords if k in line)
            validation_context = (line, test_name, matched_keyword, description)
            self._check_descriptive_comment(status, validation_context, config)

    def _check_descriptive_comment(
        self,
        status: AAAStatus,
        validation_context: tuple[str, str, str, str],
        config: DrillSergeantConfig,
    ) -> None:
        """Check if a comment line has descriptive content."""
        line, test_name, section, description = validation_context
        if not _has_descriptive_comment(line, config.min_description_length):
            status.issues.append(
                ValidationIssue(
                    issue_type="aaa",
                    message=f"Test '{test_name}' has '{section}' but missing descriptive comment",
                    suggestion=f"Add '# {section} - description of what {description}' with at least {config.min_description_length} characters",
                )
            )

    def _add_missing_section_issues(
        self, aaa_status: AAAStatus, test_name: str, issues: list[ValidationIssue]
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


def _validate_aaa_structure(
    item: pytest.Item, config: DrillSergeantConfig
) -> list[ValidationIssue]:
    """Validate AAA structure and return issues (don't fail immediately)."""
    validator = AAAValidator()
    return validator.validate(item, config)


def _has_descriptive_comment(line: str, min_length: int = 3) -> bool:
    """Check if a comment line has a descriptive dash and text."""
    # Remove the comment marker and check for dash and text
    comment_part = line.lstrip("#").strip()

    # Must have a dash followed by meaningful text
    if " - " not in comment_part:
        return False

    description = comment_part.split(" - ")[1].strip()
    return len(description) >= min_length
