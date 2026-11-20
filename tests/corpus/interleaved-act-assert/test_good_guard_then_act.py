"""Near-misses: a guard assertion on the starting state, then one act and its
assertions. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_add_item(cart):
    assert cart.items == []
    cart.add("apple")
    assert cart.items == ["apple"]


async def test_open(conn):
    assert not conn.is_open
    await conn.open()
    assert conn.is_open
