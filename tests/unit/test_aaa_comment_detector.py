"""Tests for the AAA Comment Detector."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pytest_drill_sergeant.core.analyzers.aaa_comment_detector import (
    AAACommentDetector,
    AAAResult,
)
from pytest_drill_sergeant.core.models import Severity


class TestAAACommentDetector:
    """Test the AAA Comment Detector functionality."""

    def test_init(self) -> None:
        """Test detector initialization."""
        detector = AAACommentDetector()
        assert detector is not None
        assert detector.logger is not None

    def test_rule_spec(self) -> None:
        """Test rule specification."""
        detector = AAACommentDetector()
        rule_spec = detector._get_rule_spec()
        
        assert rule_spec.code == "DS302"
        assert rule_spec.name == "aaa_comments"
        assert rule_spec.default_level == "info"
        assert "aaa" in rule_spec.long_desc.lower()
        assert "structure" in rule_spec.tags

    def test_analyze_file_correct_aaa(self) -> None:
        """Test detection with correct AAA structure."""
        detector = AAACommentDetector()

        test_code = """
def test_correct_aaa():
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 0  # No violations

    def test_analyze_file_missing_aaa(self) -> None:
        """Test detection of missing AAA comments."""
        detector = AAACommentDetector()

        test_code = """
def test_missing_aaa():
    data = {"key": "value"}
    result = process_data(data)
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS302"
            assert finding.name == "aaa_comments"
            assert finding.severity == Severity.INFO
            assert "lacks AAA comment structure" in finding.message
            assert "Add # Arrange, # Act, # Assert" in finding.suggestion

    def test_analyze_file_incorrect_order(self) -> None:
        """Test detection of incorrect AAA order."""
        detector = AAACommentDetector()

        test_code = """
def test_wrong_order():
    # Act
    result = process_data(data)
    
    # Arrange
    data = {"key": "value"}
    
    # Assert
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS302"
            assert "incorrect AAA order" in finding.message
            assert "act → arrange → assert" in finding.message

    def test_analyze_file_incomplete_aaa(self) -> None:
        """Test detection of incomplete AAA structure."""
        detector = AAACommentDetector()

        test_code = """
def test_incomplete_aaa():
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    assert result == expected  # No AAA comment here
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS302"
            assert "missing AAA sections" in finding.message
            assert "assert" in finding.message

    def test_analyze_file_duplicate_sections(self) -> None:
        """Test detection of duplicate AAA sections."""
        detector = AAACommentDetector()

        test_code = """
def test_duplicate_sections():
    # Arrange
    data = {"key": "value"}
    
    # Arrange again
    more_data = {"other": "data"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS302"
            assert "duplicate AAA sections" in finding.message
            assert "arrange" in finding.message

    def test_analyze_file_synonym_support(self) -> None:
        """Test support for AAA synonym keywords."""
        detector = AAACommentDetector()

        test_code = """
def test_synonyms():
    # Setup
    data = {"key": "value"}
    
    # When
    result = process_data(data)
    
    # Then
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 0  # No violations with synonyms

    def test_analyze_file_multiple_test_functions(self) -> None:
        """Test analysis of multiple test functions."""
        detector = AAACommentDetector()

        test_code = """
def test_good_function():
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected

def test_bad_function():
    data = {"key": "value"}
    result = process_data(data)
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1  # Only bad function should have finding
            assert "test_bad_function" in findings[0].message

    def test_analyze_file_non_test_functions_ignored(self) -> None:
        """Test that non-test functions are ignored."""
        detector = AAACommentDetector()

        test_code = """
def helper_function():
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected

def test_real_test():
    data = {"key": "value"}
    result = process_data(data)
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1  # Only test function should have finding
            assert "test_real_test" in findings[0].message

    def test_analyze_file_empty_function(self) -> None:
        """Test analysis of empty test function."""
        detector = AAACommentDetector()

        test_code = """
def test_empty():
    pass
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1
            assert "lacks AAA comment structure" in findings[0].message

    def test_analyze_file_syntax_error(self) -> None:
        """Test handling of syntax errors."""
        detector = AAACommentDetector()

        test_code = """
def test_syntax_error():
    # Arrange
    data = {"key": "value"
    # Missing closing quote and bracket
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 0  # Should gracefully handle syntax error

    def test_analyze_file_nonexistent_file(self) -> None:
        """Test handling of nonexistent file."""
        detector = AAACommentDetector()
        
        findings = detector.analyze_file(Path("nonexistent_file.py"))
        assert len(findings) == 0

    def test_analyze_file_empty_file(self) -> None:
        """Test handling of empty file."""
        detector = AAACommentDetector()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 0

    def test_analyze_file_non_python_file(self) -> None:
        """Test handling of non-Python file."""
        detector = AAACommentDetector()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is not Python code")
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 0

    def test_extract_comments(self) -> None:
        """Test comment extraction."""
        detector = AAACommentDetector()

        content = """
# This is a comment
def test_function():
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected
"""

        comments = detector._extract_comments(content)
        
        assert 2 in comments  # First comment
        assert 4 in comments  # Arrange comment
        assert 7 in comments  # Act comment
        assert 10 in comments  # Assert comment
        
        assert comments[4] == "arrange"
        assert comments[7] == "act"
        assert comments[10] == "assert"

    def test_identify_aaa_section(self) -> None:
        """Test AAA section identification."""
        detector = AAACommentDetector()

        # Test arrange variations
        assert detector._identify_aaa_section("arrange") == "arrange"
        assert detector._identify_aaa_section("setup") == "arrange"
        assert detector._identify_aaa_section("given") == "arrange"
        assert detector._identify_aaa_section("prepare") == "arrange"
        assert detector._identify_aaa_section("initialize") == "arrange"

        # Test act variations
        assert detector._identify_aaa_section("act") == "act"
        assert detector._identify_aaa_section("when") == "act"
        assert detector._identify_aaa_section("execute") == "act"
        assert detector._identify_aaa_section("perform") == "act"
        assert detector._identify_aaa_section("run") == "act"

        # Test assert variations
        assert detector._identify_aaa_section("assert") == "assert"
        assert detector._identify_aaa_section("then") == "assert"
        assert detector._identify_aaa_section("verify") == "assert"
        assert detector._identify_aaa_section("check") == "assert"
        assert detector._identify_aaa_section("expect") == "assert"

        # Test with punctuation
        assert detector._identify_aaa_section("arrange:") == "arrange"
        assert detector._identify_aaa_section("act -") == "act"
        assert detector._identify_aaa_section("assert.") == "assert"

        # Test non-AAA comments
        assert detector._identify_aaa_section("some other comment") is None
        assert detector._identify_aaa_section("arrangement") is None  # Partial match

    def test_is_correct_order(self) -> None:
        """Test order validation."""
        detector = AAACommentDetector()

        # Correct orders
        assert detector._is_correct_order(["arrange", "act", "assert"]) is True
        assert detector._is_correct_order(["arrange", "act"]) is True
        assert detector._is_correct_order(["act", "assert"]) is True
        assert detector._is_correct_order(["arrange", "assert"]) is True

        # Incorrect orders
        assert detector._is_correct_order(["act", "arrange", "assert"]) is False
        assert detector._is_correct_order(["assert", "arrange", "act"]) is False
        assert detector._is_correct_order(["assert", "act", "arrange"]) is False

        # Duplicates (should be handled gracefully)
        assert detector._is_correct_order(["arrange", "act", "arrange", "assert"]) is False
        assert detector._is_correct_order(["arrange", "arrange", "act", "assert"]) is False

    def test_analyze_aaa_structure(self) -> None:
        """Test AAA structure analysis."""
        detector = AAACommentDetector()

        # Mock function node
        func_node = type("MockNode", (), {
            "lineno": 1,
            "end_lineno": 10,
            "name": "test_function"
        })()

        # Test with correct structure
        comments = {
            2: "arrange",
            5: "act",
            8: "assert"
        }

        result = detector._analyze_aaa_structure(func_node, comments)
        
        assert isinstance(result, AAAResult)
        assert result.has_aaa_comments is True
        assert result.correct_order is True
        assert result.found_order == ["arrange", "act", "assert"]
        assert len(result.sections) == 3
        assert len(result.missing_sections) == 0
        assert len(result.duplicate_sections) == 0

    def test_analyze_aaa_structure_missing_sections(self) -> None:
        """Test AAA structure analysis with missing sections."""
        detector = AAACommentDetector()

        func_node = type("MockNode", (), {
            "lineno": 1,
            "end_lineno": 10,
            "name": "test_function"
        })()

        # Only arrange and act
        comments = {
            2: "arrange",
            5: "act"
        }

        result = detector._analyze_aaa_structure(func_node, comments)
        
        assert result.has_aaa_comments is True
        assert result.correct_order is True
        assert result.found_order == ["arrange", "act"]
        assert "assert" in result.missing_sections
        assert len(result.duplicate_sections) == 0

    def test_analyze_aaa_structure_duplicates(self) -> None:
        """Test AAA structure analysis with duplicate sections."""
        detector = AAACommentDetector()

        func_node = type("MockNode", (), {
            "lineno": 1,
            "end_lineno": 15,
            "name": "test_function"
        })()

        # Duplicate arrange sections
        comments = {
            2: "arrange",
            5: "arrange",
            8: "act",
            11: "assert"
        }

        result = detector._analyze_aaa_structure(func_node, comments)
        
        assert result.has_aaa_comments is True
        assert result.correct_order is False  # Duplicates make order incorrect
        assert "arrange" in result.duplicate_sections
        assert len(result.missing_sections) == 0

    def test_extract_aaa_sections_from_comment(self) -> None:
        """Test extraction of multiple AAA sections from a single comment."""
        detector = AAACommentDetector()

        # Test single section
        assert detector._extract_aaa_sections_from_comment("act - need to call this method") == ["act"]
        assert detector._extract_aaa_sections_from_comment("arrange data") == ["arrange"]
        assert detector._extract_aaa_sections_from_comment("assert result") == ["assert"]

        # Test multiple sections on one line
        assert detector._extract_aaa_sections_from_comment("arrange, act, assert") == ["arrange", "act", "assert"]
        assert detector._extract_aaa_sections_from_comment("setup, when, then") == ["arrange", "act", "assert"]

        # Test with punctuation and additional text
        assert detector._extract_aaa_sections_from_comment("act: do something") == ["act"]
        assert detector._extract_aaa_sections_from_comment("act. do something") == ["act"]
        assert detector._extract_aaa_sections_from_comment("act - do something") == ["act"]

        # Test mixed sections
        assert detector._extract_aaa_sections_from_comment("arrange data and act on it") == ["arrange", "act"]

        # Test non-AAA comments (should not match)
        assert detector._extract_aaa_sections_from_comment("actually this is not an aaa comment") == []
        assert detector._extract_aaa_sections_from_comment("acting on the data") == []
        assert detector._extract_aaa_sections_from_comment("arrangement of data") == []

    def test_analyze_file_multi_section_comments(self) -> None:
        """Test detection with multiple AAA sections in single comments."""
        detector = AAACommentDetector()

        test_code = '''
def test_multi_section_comment():
    # Arrange, Act, Assert - all in one line
    data = {"key": "value"}
    
    # Act - need to call this method to do something
    result = process_data(data)
    
    # Assert result is correct
    assert result == expected
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1  # Should find duplicate sections

            finding = findings[0]
            assert finding.code == "DS302"
            assert "duplicate AAA sections" in finding.message

    def test_analyze_file_mixed_aaa_sections(self) -> None:
        """Test detection with mixed AAA sections in comments."""
        detector = AAACommentDetector()

        test_code = '''
def test_mixed_sections():
    # Setup data and Act on it - mixed sections
    data = {"key": "value"}
    
    # When we call the method, Then verify
    result = process_data(data)
    assert result == expected
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1  # Should find duplicate sections

            finding = findings[0]
            assert finding.code == "DS302"
            assert "duplicate AAA sections" in finding.message

    def test_analyze_file_non_aaa_comments(self) -> None:
        """Test that non-AAA comments are properly ignored."""
        detector = AAACommentDetector()

        test_code = '''
def test_non_aaa_comments():
    # Actually this is not an AAA comment
    data = {"key": "value"}
    
    # Acting on the data
    result = process_data(data)
    
    # Assertion about the result
    assert result == expected
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))
            assert len(findings) == 1  # Should find missing AAA structure

            finding = findings[0]
            assert finding.code == "DS302"
            assert "lacks AAA comment structure" in finding.message

    def test_confidence_levels(self) -> None:
        """Test that different violations have appropriate confidence levels."""
        detector = AAACommentDetector()

        # Test missing AAA (should have high confidence)
        test_code_missing = """
def test_missing():
    data = {"key": "value"}
    result = process_data(data)
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code_missing)
            f.flush()
            findings = detector.analyze_file(Path(f.name))
            
        assert len(findings) == 1
        assert findings[0].confidence == 0.9  # High confidence for missing AAA

        # Test incorrect order (should have medium-high confidence)
        test_code_order = """
def test_wrong_order():
    # Act
    result = process_data(data)
    
    # Arrange
    data = {"key": "value"}
    
    # Assert
    assert result == expected
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code_order)
            f.flush()
            findings = detector.analyze_file(Path(f.name))
            
        assert len(findings) == 1
        assert findings[0].confidence == 0.8  # Medium-high confidence for wrong order
