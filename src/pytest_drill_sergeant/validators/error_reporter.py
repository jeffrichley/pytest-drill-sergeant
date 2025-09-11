"""Error reporting for pytest-drill-sergeant."""

import pytest

from pytest_drill_sergeant.models import ValidationIssue


class ErrorReporter:
    """Handles comprehensive error reporting for validation issues."""

    def report_issues(self, item: pytest.Item, issues: list[ValidationIssue]) -> None:
        """Report validation issues using Google-style comprehensive error reporting."""
        lines: list[str] = []

        # Categorize issues
        marker_issues = [i for i in issues if i.issue_type == "marker"]
        aaa_issues = [i for i in issues if i.issue_type == "aaa"]

        # Build header
        self._add_error_header(lines, item.name, marker_issues, aaa_issues, len(issues))

        # Add specific issue details
        self._add_issue_details(lines, marker_issues, aaa_issues)

        # Add footer with requirements explanation
        self._add_error_footer(lines)

        pytest.fail("\n".join(lines))

    def _add_error_header(
        self,
        lines: list[str],
        test_name: str,
        marker_issues: list[ValidationIssue],
        aaa_issues: list[ValidationIssue],
        total_issues: int,
    ) -> None:
        """Add error message header."""
        violations = []
        if marker_issues:
            violations.append("missing test annotations")
        if aaa_issues:
            violations.append("missing AAA structure")

        violation_text = " and ".join(violations)
        lines.append(
            f"❌ CODE QUALITY: Test '{test_name}' violates project standards by {violation_text}"
        )
        lines.append(
            f"📋 {total_issues} requirement(s) must be fixed before this test can run:"
        )
        lines.append("")

    def _add_issue_details(
        self,
        lines: list[str],
        marker_issues: list[ValidationIssue],
        aaa_issues: list[ValidationIssue],
    ) -> None:
        """Add specific issue details to error message."""
        if marker_issues:
            lines.append("🏷️  MISSING TEST CLASSIFICATION:")
            lines.extend(f"   • {issue.suggestion}" for issue in marker_issues)
            lines.append("")

        if aaa_issues:
            lines.append("📝 MISSING AAA STRUCTURE (Arrange-Act-Assert):")
            lines.extend(f"   • {issue.suggestion}" for issue in aaa_issues)
            lines.append("")

    def _add_error_footer(self, lines: list[str]) -> None:
        """Add error message footer with requirements explanation."""
        lines.append("ℹ️  This is a PROJECT REQUIREMENT for all tests to ensure:")
        lines.append("   • Consistent test structure and readability")
        lines.append("   • Proper test categorization for CI/CD pipelines")
        lines.append("   • Maintainable test suite following industry standards")
        lines.append("")
        lines.append("📚 For examples and detailed requirements:")
        lines.append("   • https://github.com/jeffrichley/pytest-drill-sergeant")
        lines.append("   • pytest.ini (for valid markers)")


def _report_all_issues(item: pytest.Item, issues: list[ValidationIssue]) -> None:
    """Report validation issues using Google-style comprehensive error reporting."""
    reporter = ErrorReporter()
    reporter.report_issues(item, issues)
