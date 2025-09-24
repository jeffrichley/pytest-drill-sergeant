"""AAA Comment Detector for pytest-drill-sergeant.

This module implements AST-based detection of AAA (Arrange-Act-Assert) comment structure
in test functions, providing advisory feedback to improve test readability and structure.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.rulespec import RuleRegistry, RuleSpec


@dataclass
class AAAResult:
    """Result of AAA analysis for a test function."""
    
    has_aaa_comments: bool
    correct_order: bool
    found_order: list[str]
    sections: list[tuple[str, int]]  # (section_type, line_number)
    missing_sections: list[str]
    duplicate_sections: list[str]


class AAACommentDetector:
    """Detects AAA comment structure in test functions using AST analysis."""

    # AAA comment keywords and synonyms
    AAA_KEYWORDS = {
        "arrange": ["arrange", "setup", "given", "prepare", "initialize"],
        "act": ["act", "when", "execute", "perform", "run"],
        "assert": ["assert", "then", "verify", "check", "expect"]
    }

    def __init__(self) -> None:
        """Initialize the AAA comment detector."""
        self.logger = logging.getLogger("drill_sergeant.aaa_comment_detector")

    def _get_rule_spec(self) -> RuleSpec:
        """Get the rule specification for AAA comment detection.

        Returns:
            Rule specification for AAA comment detection
        """
        try:
            return RuleRegistry.get_rule("DS302")  # AAA comments rule code
        except KeyError:
            # Fallback if rule not found
            from pytest_drill_sergeant.core.rulespec import RuleCategory, RuleSpec
            from pytest_drill_sergeant.core.rulespec import Severity as RuleSeverity

            return RuleSpec(
                code="DS302",
                name="aaa_comments",
                default_level=RuleSeverity.INFO,
                short_desc="Check for Arrange-Act-Assert pattern in tests",
                long_desc="Validates that tests follow the AAA pattern with clear sections for setup, execution, and verification. Improves test readability and structure.",
                tags=["structure", "readability", "best_practices"],
                fixable=False,
                category=RuleCategory.CODE_QUALITY,
            )

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for AAA comment violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for AAA comment violations
        """
        findings: list[Finding] = []
        
        try:
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return findings

            if not file_path.suffix == ".py":
                self.logger.debug(f"Skipping non-Python file: {file_path}")
                return findings

            # Read and parse the file
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                self.logger.debug(f"Empty file: {file_path}")
                return findings

            # Extract comments with line numbers
            comments = self._extract_comments(content)
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                return findings

            # Find test functions and analyze them
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    func_findings = self._analyze_test_function(
                        node, comments, file_path
                    )
                    findings.extend(func_findings)

            self.logger.debug(f"AAA analysis of {file_path}: {len(findings)} findings")

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
            # Return empty findings rather than crashing

        return findings

    def _extract_comments(self, content: str) -> dict[int, str]:
        """Extract comments with line numbers and normalize text.
        
        Args:
            content: File content as string
            
        Returns:
            Dictionary mapping line numbers to normalized comment text
        """
        comments: dict[int, str] = {}
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Find comment start
            comment_start = line.find("#")
            if comment_start != -1:
                comment_text = line[comment_start + 1:].strip()
                if comment_text:
                    # Normalize comment text
                    normalized = comment_text.lower().strip()
                    comments[i] = normalized
                    
        return comments

    def _analyze_test_function(
        self, 
        func_node: ast.FunctionDef, 
        comments: dict[int, str], 
        file_path: Path
    ) -> list[Finding]:
        """Analyze AAA structure of a test function.
        
        Args:
            func_node: AST node for the test function
            comments: Dictionary of comments by line number
            file_path: Path to the file being analyzed
            
        Returns:
            List of findings for this function
        """
        findings: list[Finding] = []
        
        # Get function boundaries
        func_start = func_node.lineno
        func_end = func_node.end_lineno or func_start
        
        # Extract AAA comments within function
        aaa_result = self._analyze_aaa_structure(func_node, comments)
        
        # Create a comprehensive AAA status message
        status_parts = []
        all_sections = {"arrange", "act", "assert"}
        
        for section in ["arrange", "act", "assert"]:
            if section in aaa_result.found_order:
                status_parts.append(f"✅ {section.title()}")
            else:
                status_parts.append(f"❌ {section.title()}")
        
        status_message = " | ".join(status_parts)
        
        if not aaa_result.has_aaa_comments:
            # No AAA comments found
            finding = Finding(
                code="DS302",
                name="aaa_comments",
                severity=Severity.INFO,
                message=f"Test '{func_node.name}' lacks AAA comment structure: {status_message}",
                suggestion="Add # Arrange, # Act, # Assert comments to improve test readability",
                file_path=file_path,
                line_number=func_start,
                confidence=0.9,
                fixable=False,
                tags=["structure", "readability"]
            )
            findings.append(finding)
            
        elif aaa_result.duplicate_sections:
            # Duplicate sections
            duplicate_str = ", ".join(aaa_result.duplicate_sections)
            finding = Finding(
                code="DS302",
                name="aaa_comments",
                severity=Severity.INFO,
                message=f"Test '{func_node.name}' has duplicate AAA sections: {duplicate_str} | {status_message}",
                suggestion="Remove duplicate AAA comment sections",
                file_path=file_path,
                line_number=func_start,
                confidence=0.6,
                fixable=False,
                tags=["structure", "readability"]
            )
            findings.append(finding)
            
        elif not aaa_result.correct_order:
            # Incorrect order
            found_order_str = " → ".join(aaa_result.found_order)
            finding = Finding(
                code="DS302",
                name="aaa_comments",
                severity=Severity.INFO,
                message=f"Test '{func_node.name}' has incorrect AAA order: {found_order_str} | {status_message}",
                suggestion="Reorder comments to follow Arrange → Act → Assert pattern",
                file_path=file_path,
                line_number=func_start,
                confidence=0.8,
                fixable=False,
                tags=["structure", "readability"]
            )
            findings.append(finding)
            
        elif aaa_result.missing_sections:
            # Missing sections (partial AAA structure)
            missing_str = ", ".join(aaa_result.missing_sections)
            finding = Finding(
                code="DS302",
                name="aaa_comments",
                severity=Severity.INFO,
                message=f"Test '{func_node.name}' missing AAA sections: {missing_str} | {status_message}",
                suggestion="Add missing AAA comment sections",
                file_path=file_path,
                line_number=func_start,
                confidence=0.7,
                fixable=False,
                tags=["structure", "readability"]
            )
            findings.append(finding)
            
        return findings

    def _analyze_aaa_structure(
        self, 
        func_node: ast.FunctionDef, 
        comments: dict[int, str]
    ) -> AAAResult:
        """Analyze AAA structure of a test function.
        
        Args:
            func_node: AST node for the test function
            comments: Dictionary of comments by line number
            
        Returns:
            AAAResult with analysis details
        """
        func_start = func_node.lineno
        func_end = func_node.end_lineno or func_start
        
        # Find comments within function body
        func_comments = {
            line_num: comment 
            for line_num, comment in comments.items()
            if func_start <= line_num <= func_end
        }
        
        # Identify AAA sections
        sections: list[tuple[str, int]] = []
        found_sections = set()
        
        for line_num, comment in func_comments.items():
            # Extract all AAA sections from this comment line
            section_types = self._extract_aaa_sections_from_comment(comment)
            for section_type in section_types:
                sections.append((section_type, line_num))
                found_sections.add(section_type)
        
        # Check for duplicates
        duplicate_sections = []
        section_counts = {}
        for section_type, _ in sections:
            section_counts[section_type] = section_counts.get(section_type, 0) + 1
            if section_counts[section_type] > 1:
                duplicate_sections.append(section_type)
        
        # Determine missing sections
        all_sections = {"arrange", "act", "assert"}
        missing_sections = list(all_sections - found_sections)
        
        # Check order
        found_order = [section_type for section_type, _ in sections]
        correct_order = self._is_correct_order(found_order)
        
        return AAAResult(
            has_aaa_comments=len(sections) > 0,
            correct_order=correct_order,
            found_order=found_order,
            sections=sections,
            missing_sections=missing_sections,
            duplicate_sections=duplicate_sections
        )

    def _identify_aaa_section(self, comment: str) -> str | None:
        """Identify if a comment represents an AAA section.
        
        Args:
            comment: Normalized comment text
            
        Returns:
            Section type ('arrange', 'act', 'assert') or None
        """
        # Remove common prefixes and normalize
        comment = re.sub(r"^#\s*", "", comment)
        comment = comment.strip()
        
        # Check against all keywords
        for section_type, keywords in self.AAA_KEYWORDS.items():
            for keyword in keywords:
                # Check if comment starts with keyword followed by word boundary
                # This handles cases like "Act - need to call this method"
                if re.match(rf"^{keyword}\b", comment):
                    # Additional validation: ensure it's an explicit AAA marker
                    # Must have meaningful content after the keyword (not just the keyword alone)
                    remaining_text = comment[len(keyword):].strip()
                    
                    # Skip if it's just the keyword alone or with minimal content
                    if len(remaining_text) < 3:
                        continue
                    
                    # Skip if it looks like a regular sentence that happens to start with the keyword
                    # (e.g., "when run under pytest..." should not be an "act" section)
                    if remaining_text.startswith(("run ", "is ", "are ", "was ", "were ", "will ", "would ", "should ", "could ", "might ", "may ")):
                        continue
                    
                    return section_type
                        
        return None

    def _extract_aaa_sections_from_comment(self, comment: str) -> list[str]:
        """Extract all AAA sections from a single comment line.
        
        This handles cases like "# Arrange, Act, Assert" or "# Act - need to call this method"
        Requires meaningful content after the keyword (not just "# Act" alone).
        
        Args:
            comment: Comment text to analyze
            
        Returns:
            List of section types found in the comment
        """
        sections_found = []
        
        # Remove comment prefix and normalize
        comment = re.sub(r"^#\s*", "", comment)
        comment = comment.strip()
        
        # Check each keyword - must be at the start of the comment
        for section_type, keywords in self.AAA_KEYWORDS.items():
            for keyword in keywords:
                # Look for the keyword at the start of the comment with word boundaries
                if re.match(rf"^{keyword}\b", comment):
                    # Check if there's meaningful content after the keyword
                    remaining_text = comment[len(keyword):].strip()
                    
                    # Skip if it's just the keyword alone or with minimal content
                    if len(remaining_text) < 3:
                        continue
                    
                    # Skip if it looks like a regular sentence that happens to start with the keyword
                    if remaining_text.startswith(("run ", "is ", "are ", "was ", "were ", "will ", "would ", "should ", "could ", "might ", "may ")):
                        continue
                    
                    sections_found.append(section_type)
                    break  # Only add each section type once per comment
        
        return sections_found

    def _has_meaningful_content(self, comment: str, keyword: str) -> bool:
        """Check if comment has meaningful content after the keyword.
        
        Args:
            comment: Full comment text
            keyword: The AAA keyword found
            
        Returns:
            True if there's meaningful content after the keyword
        """
        # Find the position of the keyword
        keyword_match = re.search(rf"\b{keyword}\b", comment)
        if not keyword_match:
            return False
            
        # Get text after the keyword
        after_keyword = comment[keyword_match.end():].strip()
        
        # Remove common separators and check for meaningful content
        after_keyword = re.sub(r"^[,\-\s&]+", "", after_keyword).strip()
        
        # Check if there's meaningful content (not just other AAA keywords)
        if len(after_keyword) < 3:
            return False
            
        # Check if the remaining text is just other AAA keywords
        other_keywords = []
        for section_type, keywords in self.AAA_KEYWORDS.items():
            if section_type != keyword:
                other_keywords.extend(keywords)
        
        # If what's left is just other AAA keywords, it's not meaningful
        remaining_words = after_keyword.lower().split()
        if all(word in other_keywords for word in remaining_words):
            return False
            
        return True

    def _is_correct_order(self, found_order: list[str]) -> bool:
        """Check if the found order follows AAA pattern.
        
        Args:
            found_order: List of section types in order they appear
            
        Returns:
            True if order is correct (arrange -> act -> assert)
        """
        # Remove duplicates while preserving order
        seen = set()
        unique_order = []
        for section in found_order:
            if section not in seen:
                unique_order.append(section)
                seen.add(section)
        
        # Check if it follows the pattern
        expected_order = ["arrange", "act", "assert"]
        
        # Find positions of each section in the found order
        positions = {}
        for i, section in enumerate(unique_order):
            if section in expected_order:
                positions[section] = i
        
        # Check if arrange comes before act, and act comes before assert
        if "arrange" in positions and "act" in positions:
            if positions["arrange"] >= positions["act"]:
                return False
                
        if "act" in positions and "assert" in positions:
            if positions["act"] >= positions["assert"]:
                return False
                
        if "arrange" in positions and "assert" in positions:
            if positions["arrange"] >= positions["assert"]:
                return False
        
        # If we have duplicates in the original order, it's incorrect
        if len(found_order) != len(unique_order):
            return False
                
        return True
