"""The golden suite's inventory tests: the one file past the suite's file limit.

Analysed by the golden test, never run.
"""

import pytest

from shop.inventory import Inventory, OutOfStock

pytestmark = pytest.mark.unit


@pytest.fixture
def stocked():
    inventory = Inventory()
    inventory.restock("apple", 5)
    return inventory


def test_restocking_raises_the_count():
    inventory = Inventory()

    inventory.restock("pear", 4)

    assert inventory.count("pear") == 4


def test_reserving_holds_items_back_from_sale(stocked):
    stocked.reserve("apple", 2)

    assert stocked.available("apple") == 3


def test_reserving_more_than_is_in_stock_is_refused(stocked):
    with pytest.raises(OutOfStock, match="apple"):
        stocked.reserve("apple", 6)


def test_an_unknown_item_counts_as_none():
    assert Inventory().count("durian") == 0


def test_releasing_a_reservation_returns_it_to_sale(stocked):
    stocked.reserve("apple", 2)

    stocked.release("apple", 2)

    assert stocked.available("apple") == 5
