"""Tests that act, assert, then act and assert again: two behaviours in one test.
Analysed, never run."""


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
