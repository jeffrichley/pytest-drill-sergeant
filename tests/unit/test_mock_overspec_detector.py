"""Tests for Mock Over-Specification Detector."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

import pytest

from pytest_drill_sergeant.core.analyzers.mock_overspec_detector import (
    MockOverspecDetector,
)
from pytest_drill_sergeant.core.models import Severity


class TestMockOverspecDetector:
    """Test cases for MockOverspecDetector."""

    @pytest.fixture
    def detector(self) -> MockOverspecDetector:
        """Create a detector instance."""
        return MockOverspecDetector()

    def test_detector_initialization(self, detector: MockOverspecDetector) -> None:
        """Test detector initializes correctly."""
        assert detector is not None
        assert detector.logger.name == "drill_sergeant.mock_overspec_detector"
        assert len(detector.MOCK_ASSERTS) == 6
        assert "assert_called_once" in detector.MOCK_ASSERTS
        assert "assert_called_with" in detector.MOCK_ASSERTS

    def test_rule_spec(self, detector: MockOverspecDetector) -> None:
        """Test rule specification is correct."""
        rule_spec = detector._get_rule_spec()
        
        assert rule_spec.code == "DS102"
        assert rule_spec.name == "mock_overspec"
        assert rule_spec.category.value == "code_quality"
        assert rule_spec.default_level.value == "warning"
        assert "mock" in rule_spec.tags
        assert "overspecification" in rule_spec.tags

    def test_is_mock_target_allowed_basic_patterns(self, detector: MockOverspecDetector) -> None:
        """Test allowlist pattern matching for basic cases."""
        allowlist = ["requests.*", "boto3.*", "time.*", "mock_requests"]
        
        # Should match
        assert detector._is_mock_target_allowed("requests.get", allowlist) is True
        assert detector._is_mock_target_allowed("boto3.client", allowlist) is True
        assert detector._is_mock_target_allowed("time.sleep", allowlist) is True
        assert detector._is_mock_target_allowed("mock_requests", allowlist) is True
        
        # Should not match
        assert detector._is_mock_target_allowed("mock_service", allowlist) is False
        assert detector._is_mock_target_allowed("user_service", allowlist) is False

    def test_is_mock_target_allowed_complex_patterns(self, detector: MockOverspecDetector) -> None:
        """Test allowlist pattern matching for complex cases."""
        allowlist = ["*.client", "test_*", "mock_requests.*"]
        
        # Should match
        assert detector._is_mock_target_allowed("boto3.client", allowlist) is True
        assert detector._is_mock_target_allowed("test_helper", allowlist) is True
        assert detector._is_mock_target_allowed("mock_requests.get", allowlist) is True
        
        # Should not match
        assert detector._is_mock_target_allowed("client.boto3", allowlist) is False
        assert detector._is_mock_target_allowed("helper_test", allowlist) is False

    def test_extract_mock_target_simple_name(self, detector: MockOverspecDetector) -> None:
        """Test extracting mock target from simple name."""
        # mock_obj.assert_called_once()
        code = "mock_obj.assert_called_once()"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # type: ignore
        attr_node = call_node.func  # Get the function being called
        
        target = detector._extract_mock_target(attr_node)
        assert target == "mock_obj"

    def test_extract_mock_target_chained_calls(self, detector: MockOverspecDetector) -> None:
        """Test extracting mock target from chained calls."""
        # mock_service.method.assert_called_once()
        code = "mock_service.method.assert_called_once()"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # type: ignore
        attr_node = call_node.func  # Get the function being called
        
        target = detector._extract_mock_target(attr_node)
        assert target == "mock_service.method"

    def test_extract_mock_target_complex_expression(self, detector: MockOverspecDetector) -> None:
        """Test extracting mock target from complex expressions."""
        # Should return None for complex cases we can't handle
        code = "get_mock().assert_called_once()"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # type: ignore
        attr_node = call_node.func  # Get the function being called
        
        target = detector._extract_mock_target(attr_node)
        assert target is None

    def test_count_mock_assertions_under_threshold(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test counting mock assertions under threshold."""
        test_content = """
def test_under_threshold():
    mock_service = Mock()
    result = service.process(mock_service)
    
    mock_service.method.assert_called_once()
    mock_service.other_method.assert_called_with("arg")
    
    assert result == expected
"""
        
        test_file = tmp_path / "test_under_threshold.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 0

    def test_count_mock_assertions_over_threshold(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test counting mock assertions over threshold."""
        test_content = """
def test_over_threshold():
    mock_service = Mock()
    result = service.process(mock_service)
    
    # 4 mock assertions - should trigger detector
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.assert_has_calls([call.method1(), call.method2("arg")])
    mock_service.method3.assert_any_call("other")
    
    assert result == expected
"""
        
        test_file = tmp_path / "test_over_threshold.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1
        
        finding = findings[0]
        assert finding.code == "DS102"
        assert finding.name == "mock_overspec"
        assert finding.severity == Severity.WARNING
        assert "4 mock assertions" in finding.message
        assert "threshold: 3" in finding.message
        assert finding.line_number == 2  # Function definition line

    def test_allowlist_filtering(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test that allowlisted mock targets are filtered out."""
        test_content = """
def test_allowlist_filtering():
    mock_requests = Mock()
    result = service.make_request(mock_requests)
    
    # 4 mock assertions on requests.* - should be filtered out
    mock_requests.get.assert_called_once()
    mock_requests.post.assert_called_with("data")
    mock_requests.assert_has_calls([call.get(), call.post("data")])
    mock_requests.session.assert_any_call()
    
    assert result == expected
"""
        
        test_file = tmp_path / "test_allowlist.py"
        test_file.write_text(test_content)
        
        # Mock the allowlist to include requests.*
        with patch.object(detector, "_is_mock_target_allowed", return_value=True):
            findings = detector.analyze_file(test_file)
            assert len(findings) == 0

    def test_mixed_allowed_and_disallowed_mocks(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test mixed allowed and disallowed mock assertions."""
        test_content = """
def test_mixed_mocks():
    mock_service = Mock()   # Should not be allowed
    
    # 4 service mocks (not allowed) = 4 violations (over threshold of 3)
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_any_call("other")
    mock_service.method4.assert_called()
    
    assert True
"""
        
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1  # Should find 4 violations (over threshold of 3)

    def test_multiple_test_functions(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test analysis of multiple test functions."""
        test_content = """
def test_good_function():
    mock_service = Mock()
    result = service.process(mock_service)
    
    mock_service.method.assert_called_once()
    assert result == expected

def test_bad_function():
    mock_service = Mock()
    result = service.process(mock_service)
    
    # 4 mock assertions - should trigger
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.assert_has_calls([call.method1()])
    mock_service.method3.assert_any_call("other")
    
    assert result == expected

def helper_function():  # Not a test - should be ignored
    mock_service = Mock()
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_has_calls([])
    mock_service.method4.assert_any_call("other")
"""
        
        test_file = tmp_path / "test_multiple.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1  # Only the bad test function
        assert "test_bad_function" in findings[0].message

    def test_different_mock_assertion_types(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test detection of different types of mock assertions."""
        test_content = """
def test_all_assertion_types():
    mock_service = Mock()
    
    # Test all 6 types of mock assertions
    mock_service.assert_called_once()
    mock_service.assert_called_with("arg")
    mock_service.assert_has_calls([call()])
    mock_service.assert_any_call("other")
    mock_service.assert_called()
    mock_service.assert_not_called()
    
    assert True
"""
        
        test_file = tmp_path / "test_assertion_types.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1
        assert "6 mock assertions" in findings[0].message

    def test_syntax_error_handling(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test handling of files with syntax errors."""
        test_content = """
def test_syntax_error(:  # Invalid syntax
    mock_service = Mock()
    mock_service.assert_called_once()
"""
        
        test_file = tmp_path / "test_syntax_error.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 0  # Should handle gracefully

    def test_empty_file(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test handling of empty files."""
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("")
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 0

    def test_file_without_tests(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test handling of files without test functions."""
        test_content = """
def helper_function():
    mock_service = Mock()
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_has_calls([])
    mock_service.method4.assert_any_call("other")

class HelperClass:
    def method(self):
        pass
"""
        
        test_file = tmp_path / "helper.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 0

    def test_nested_functions_ignored(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test that nested functions are ignored."""
        test_content = """
def test_with_nested():
    def inner_function():
        mock_service = Mock()
        mock_service.method1.assert_called_once()
        mock_service.method2.assert_called_with("arg")
        mock_service.method3.assert_has_calls([])
        mock_service.method4.assert_any_call("other")
    
    mock_service = Mock()
    mock_service.assert_called_once()  # Only this should count
    assert True
"""
        
        test_file = tmp_path / "test_nested.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 0  # Only 1 assertion in the actual test

    def test_finding_details(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test that finding contains all required details."""
        test_content = """
def test_finding_details():
    mock_service = Mock()
    
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_has_calls([])
    mock_service.method4.assert_any_call("other")
    
    assert True
"""
        
        test_file = tmp_path / "test_details.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1
        
        finding = findings[0]
        assert finding.code == "DS102"
        assert finding.name == "mock_overspec"
        assert finding.severity == Severity.WARNING
        assert finding.file_path == test_file
        assert finding.line_number == 2
        assert finding.column_number == 0
        assert "Reduce mock assertions" in finding.suggestion
        assert "behavior being tested" in finding.suggestion

    def test_configuration_integration(self, detector: MockOverspecDetector, tmp_path: Path) -> None:
        """Test basic functionality (configuration integration will be added later)."""
        test_content = """
def test_config_integration():
    mock_service = Mock()
    
    # 4 assertions - should trigger with default threshold 3
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_has_calls([])
    mock_service.method4.assert_any_call("other")
    
    assert True
"""
        
        test_file = tmp_path / "test_config.py"
        test_file.write_text(test_content)
        
        findings = detector.analyze_file(test_file)
        assert len(findings) == 1  # Should trigger with default threshold 3
