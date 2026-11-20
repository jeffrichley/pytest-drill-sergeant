"""Helpers the file defines, followed to any depth, that never assert. Analysed,
never run."""

from functools import partial

import pytest
from frames import normalise

pytestmark = pytest.mark.unit


def _render(order):
    return _format(order)


def _format(order):
    return str(order)


def _ping(n):
    return _pong(n - 1) if n else 0


def _pong(n):
    return _ping(n)


def test_a_helper_that_only_renders_checks_nothing():  # expect: DS101
    _render({"id": 1})


def test_helpers_calling_each_other_check_nothing():  # expect: DS101
    _ping(3)


def test_a_partial_of_a_helper_that_asserts_nothing_checks_nothing():  # expect: DS101
    render = partial(_render, {"id": 1})
    render()


class TestFrames:
    def setup_method(self):
        self.frame = normalise(self.frame)
        self.left = self.right
        self.right = self.left

    def test_an_attribute_set_from_itself_checks_nothing(self):  # expect: DS101
        self.frame.sum()

    def test_attributes_set_from_each_other_check_nothing(self):  # expect: DS101
        self.left()
