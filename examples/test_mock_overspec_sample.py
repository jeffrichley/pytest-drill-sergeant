"""Sample test file with mock over-specification violations for testing."""

from unittest.mock import Mock, call


def test_good_mock_usage():
    """Test with appropriate mock usage - should not trigger detector."""
    mock_service = Mock()
    mock_service.process.return_value = None
    mock_service.validate.return_value = None
    
    result = process_data(mock_service)
    
    # Only 2 mock assertions - under threshold
    mock_service.process.assert_called_once_with("data")
    mock_service.validate.assert_called_once()
    
    assert result == "processed"


def test_mock_overspecification():
    """Test with excessive mock assertions - should trigger detector."""
    mock_service = Mock()
    # Set up the mock to avoid assertion failures
    mock_service.method1.return_value = None
    mock_service.method2.return_value = None
    mock_service.method3.return_value = None
    
    result = process_data(mock_service)
    
    # 4 mock assertions - over threshold of 3
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.assert_has_calls([call.method1(), call.method2("arg")])
    mock_service.method3.assert_any_call("other")
    
    assert result == "processed"


def test_allowlisted_mock():
    """Test with allowlisted mock target - should not trigger detector."""
    mock_requests = Mock()
    
    # Set up mock returns to avoid failures
    mock_requests.get.return_value = None
    mock_requests.post.return_value = None
    mock_requests.session.return_value = None
    
    result = make_http_request(mock_requests)
    
    # 4 mock assertions on requests.* - should be filtered out by allowlist
    mock_requests.get.assert_called_once()
    mock_requests.post.assert_called_with("data")
    mock_requests.assert_has_calls([call.get(), call.post("data")])
    mock_requests.session.assert_any_call()
    
    assert result == "success"


def test_mixed_mocks():
    """Test with mixed allowed and disallowed mocks."""
    mock_service = Mock()   # Should not be allowed
    
    # Set up mock returns to avoid failures
    mock_service.method1.return_value = None
    mock_service.method2.return_value = None
    mock_service.method3.return_value = None
    
    # Call the methods so assertions don't fail
    mock_service.method1()
    mock_service.method2("arg")
    mock_service.method3("other")
    
    # 3 service mocks (not allowed) = 3 violations
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_any_call("other")
    
    assert True


def helper_function():
    """Not a test function - should be ignored."""
    mock_service = Mock()
    mock_service.method1.assert_called_once()
    mock_service.method2.assert_called_with("arg")
    mock_service.method3.assert_has_calls([])
    mock_service.method4.assert_any_call("other")
    mock_service.method5.assert_called()
    mock_service.method6.assert_not_called()


# Mock functions for testing
def process_data(service):
    """Mock function for testing."""
    # Call the mock methods that will be asserted
    service.process("data")
    service.validate()
    # For the overspec test, call the methods that will be asserted
    if hasattr(service, "method1"):
        service.method1()
    if hasattr(service, "method2"):
        service.method2("arg")
    if hasattr(service, "method3"):
        service.method3("other")
    return "processed"


def make_http_request(client):
    """Mock function for testing."""
    client.get()
    client.post("data")
    # For the allowlisted mock test, call the session method
    if hasattr(client, "session"):
        client.session()
    return "success"
