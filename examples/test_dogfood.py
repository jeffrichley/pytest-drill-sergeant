"""Test file to verify both private access and mock overspec detectors work."""

from unittest.mock import Mock


def test_with_private_access():
    """Test that accesses private attributes - should trigger private access detector."""
    obj = SomeClass()
    result = obj._private_method()  # Should trigger private access detector
    assert result == "expected"


def test_with_mock_overspec():
    """Test with excessive mock assertions - should trigger mock overspec detector."""
    mock_service = Mock()
    mock_service.method1.return_value = None
    mock_service.method2.return_value = None
    mock_service.method3.return_value = None
    mock_service.method4.return_value = None

    # Call the methods so assertions don't fail
    mock_service.method1()
    mock_service.method2("arg")
    mock_service.method3("other")
    mock_service.method4()

    # 4 mock assertions - over threshold of 3
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_any_call("other")
    mock_service.method4.assert_called()

    assert True


def test_clean_test():
    """Clean test that should not trigger any detectors."""
    result = public_function("input")
    assert result == "expected_output"


# Mock classes and functions
class SomeClass:
    def _private_method(self):
        return "expected"


def public_function(input_data):
    return "expected_output"
