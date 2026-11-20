"""Malformed waivers outside every test are reported too."""

import pytest  # drill: waive  # expect: DS001
from calc import double


def helper():  # drill: waive DS101  # expect: DS001
    return 1


@pytest.fixture
def number():
    return helper()


def test_number(number):
    assert double(number) == 2
