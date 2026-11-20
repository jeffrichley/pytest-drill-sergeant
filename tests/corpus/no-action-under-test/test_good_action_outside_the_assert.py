"""Near-misses: the action is a plain statement, a method call on a literal, or an
operator inside a `with`, not in the assertion. Analysed, never run."""

from unittest import mock

import pytest

pytestmark = pytest.mark.unit


def register(registry, name):
    registry.append(name)


def test_side_effect_then_assert():
    registry = []
    register(registry, "ada")
    assert registry == ["ada"]


def test_method_on_a_literal_is_an_action():
    parts = "a,b".split(",")
    assert parts == ["a", "b"]


def test_action_inside_a_patch():
    with mock.patch("os.getcwd", autospec=True, return_value="/tmp"):
        registry = []
        register(registry, "grace")
    assert registry == ["grace"]
