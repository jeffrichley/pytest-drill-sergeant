"""Sample test file for AAA Comment Detector testing.

This file contains various test functions demonstrating different AAA comment patterns
for testing the AAA Comment Detector functionality.
"""


def test_with_correct_aaa():
    """Test with proper AAA comment structure."""
    # Arrange
    data = {"key": "value"}
    expected = {"processed": True}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected
    assert result["processed"] is True


def test_with_synonyms():
    """Test with AAA synonym keywords."""
    # Setup
    user_data = {"name": "John", "age": 30}
    
    # When
    user = create_user(user_data)
    
    # Then
    assert user.name == "John"
    assert user.age == 30


def test_missing_aaa_comments():
    """Test without any AAA comment structure."""
    data = {"key": "value"}
    result = process_data(data)
    assert result == expected


def test_incomplete_aaa():
    """Test with incomplete AAA structure."""
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    assert result == expected  # Missing # Assert comment


def test_wrong_aaa_order():
    """Test with incorrect AAA order."""
    # Act
    result = process_data(data)
    
    # Arrange
    data = {"key": "value"}
    
    # Assert
    assert result == expected


def test_duplicate_aaa_sections():
    """Test with duplicate AAA sections."""
    # Arrange
    data = {"key": "value"}
    
    # Arrange again
    more_data = {"other": "data"}
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result == expected


def test_mixed_synonyms():
    """Test with mixed AAA keywords and synonyms."""
    # Setup
    config = load_config()
    
    # When
    service = initialize_service(config)
    
    # Then
    assert service.is_ready()


def test_partial_aaa():
    """Test with only some AAA sections."""
    # Arrange
    test_input = [1, 2, 3, 4, 5]
    
    result = calculate_sum(test_input)
    
    # Assert
    assert result == 15


def test_aaa_with_extra_comments():
    """Test with AAA comments plus other comments."""
    # Arrange
    # Load test data from fixture
    data = load_test_data()
    
    # Act
    # Process the data
    result = process_data(data)
    
    # Assert
    # Verify the result
    assert result is not None
    assert result.status == "success"


def test_edge_case_empty_function():
    """Test edge case with empty function body."""


def test_edge_case_single_line():
    """Test edge case with single line test."""
    # Arrange
    assert True


def test_edge_case_no_assertions():
    """Test edge case with no assertions."""
    # Arrange
    data = {"key": "value"}
    
    # Act
    result = process_data(data)
    
    # No assertions - just side effects


def test_complex_aaa_structure():
    """Test with complex AAA structure and nested logic."""
    # Arrange
    user_data = {
        "name": "Alice",
        "email": "alice@example.com",
        "preferences": {"theme": "dark", "notifications": True}
    }
    expected_user_id = "user_123"
    
    # Act
    user = create_user(user_data)
    user_id = user.save()
    
    # Assert
    assert user_id == expected_user_id
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.preferences["theme"] == "dark"


# Helper functions (should not be analyzed)
def process_data(data):
    """Helper function - should be ignored by AAA detector."""
    return {"processed": True}


def create_user(user_data):
    """Helper function - should be ignored by AAA detector."""
    return type("User", (), user_data)()


def load_config():
    """Helper function - should be ignored by AAA detector."""
    return {"timeout": 30}


def initialize_service(config):
    """Helper function - should be ignored by AAA detector."""
    return type("Service", (), {"is_ready": lambda: True})()


def load_test_data():
    """Helper function - should be ignored by AAA detector."""
    return {"test": "data"}


def calculate_sum(numbers):
    """Helper function - should be ignored by AAA detector."""
    return sum(numbers)
