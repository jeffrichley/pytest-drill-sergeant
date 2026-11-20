"""Tests that act, assert, then act and assert again: two behaviours in one test.
Analysed, never run."""

import logging

import pytest

pytestmark = pytest.mark.unit


def test_cart(cart):
    cart.add("apple")
    assert cart.items == ["apple"]
    cart.remove("apple")  # expect: DS104
    assert cart.items == []


def test_user_lifecycle(users):
    users.create("ada")
    assert users.exists("ada")
    users.rename("ada", "grace")  # expect: DS104
    assert users.exists("grace")
    users.delete("grace")
    assert not users.exists("grace")


def test_log_cleared_then_add_again(caplog, cart):
    caplog.set_level(logging.INFO)
    cart.add("a")
    assert "added a" in caplog.text
    caplog.clear()
    cart.add("b")  # expect: DS104
    assert "added b" in caplog.text
