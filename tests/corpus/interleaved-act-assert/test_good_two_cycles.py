"""Near-misses: two act-then-assert cycles, under the default of three that
`drill_sergeant_max_act_assert_cycles` sets. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_cart(cart):
    cart.add("apple")
    assert cart.items == ["apple"]
    cart.remove("apple")
    assert cart.items == []


async def test_door(door):
    await door.unlock()
    assert not door.locked
    await door.lock()
    assert door.locked
