"""AAA comments that match the code under them, in the forms the check accepts.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_add_item(cart):
    # Arrange
    item = "apple"
    # Act
    cart.add(item)
    # Assert
    assert cart.items == [item]


def test_total_reads_its_result(cart):
    # Arrange: two priced items
    cart.add("pear", price=3)
    cart.add("plum", price=4)
    # Act - total the cart
    total = cart.total()
    # ASSERT
    assert total == 7


async def test_fetch_page(client):
    # act
    page = await client.fetch("/home")
    # assert — the page loaded
    assert page.status == 200
    assert page.title == "Home"


def test_reorder_with_a_guard(queue_factory):
    # Arrange
    queue = queue_factory(["a", "b"])
    assert queue.peek() == "a"
    # Act
    queue.rotate()
    # Assert
    head = queue.peek()
    assert head == "b"
