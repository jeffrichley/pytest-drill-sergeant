"""Sample test file with structural equality violations."""

import dataclasses
from dataclasses import dataclass


@dataclass
class User:
    name: str
    email: str

def test_dict_comparison():
    """BAD: Testing internal structure."""
    user = User("John", "john@example.com")
    assert user.__dict__ == {"name": "John", "email": "john@example.com"}

def test_vars_comparison():
    """BAD: Testing internal structure."""
    user = User("Jane", "jane@example.com")
    assert vars(user) == {"name": "Jane", "email": "jane@example.com"}

def test_asdict_comparison():
    """BAD: Testing internal structure."""
    user = User("Bob", "bob@example.com")
    assert dataclasses.asdict(user) == {"name": "Bob", "email": "bob@example.com"}

def test_repr_comparison():
    """BAD: Testing string representation."""
    user = User("Alice", "alice@example.com")
    assert repr(user) == "User(name='Alice', email='alice@example.com')"

def test_str_comparison():
    """BAD: Testing string representation."""
    user = User("Charlie", "charlie@example.com")
    assert str(user) == "User(name='Charlie', email='charlie@example.com')"

def test_getattr_private():
    """BAD: Accessing private attributes."""
    user = User("David", "david@example.com")
    # This will fail at runtime but demonstrates the pattern
    assert getattr(user, "_private_attr", "expected_value") == "expected_value"

def test_clean_behavior_test():
    """GOOD: Testing behavior."""
    user = User("Eve", "eve@example.com")
    assert user.name == "Eve"
    assert user.email == "eve@example.com"

def test_multiple_violations():
    """BAD: Multiple structural equality violations."""
    user = User("Frank", "frank@example.com")
    assert user.__dict__ == {"name": "Frank", "email": "frank@example.com"}
    assert vars(user) == {"name": "Frank", "email": "frank@example.com"}
    assert dataclasses.asdict(user) == {"name": "Frank", "email": "frank@example.com"}

def test_non_test_function():
    """This should not be flagged as it's not a test function."""
    user = User("Grace", "grace@example.com")
    assert user.__dict__ == {"name": "Grace", "email": "grace@example.com"}

def test_nested_calls():
    """BAD: Nested structural equality calls."""
    user = User("Henry", "henry@example.com")
    expected_dict = {"name": "Henry", "email": "henry@example.com"}
    assert vars(user) == expected_dict
    assert dataclasses.asdict(user) == expected_dict
