"""Near-misses: an `assert*` function is the code under test, so calling it runs
code (#178). Modelled on stagehand `tests/test_session.py:59` and pandas
`test_assert_almost_equal.py:633`. Analysed, never run.
"""

import pytest
from app.session import assert_stable

pytestmark = pytest.mark.unit


def assert_same_length(first, second):
    if len(first) != len(second):
        raise AssertionError(f"{first!r} and {second!r} differ in length")


def test_imported_assert_function_passes():
    assert_stable("abc", "abc")


def test_imported_assert_function_raises():
    with pytest.raises(AssertionError, match="unstable"):
        assert_stable("abc", "abd")


def test_same_file_assert_function_raises():
    with pytest.raises(AssertionError, match="length"):
        assert_same_length("ab", "abc")
