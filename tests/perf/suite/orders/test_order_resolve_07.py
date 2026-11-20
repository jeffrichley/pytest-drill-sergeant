"""Tests for orders order handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_order, resolve


@pytest.fixture
def order():
    return make_order()


def test_resolve_order_large_0():
    order = make_order(amount=18, count=9)

    result = resolve(order)

    assert result.total == 162


def test_resolve_order_large_1(order):
    order.label = "batch-912"

    resolve(order)

    assert order.state == "held"


def test_resolve_order_basic_2():
    order = make_order(amount=12, count=76)

    result = resolve(order)

    assert result.total == 912


def test_resolve_order_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    resolve(repo, 115)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_order_large_4(order):
    order.label = "invoice-334"

    resolve(order)

    assert order.state == "done"


def test_resolve_order_many_5():
    order = make_order(amount=20, count=78)

    result = resolve(order)

    assert result.total == 1560


def test_resolve_order_edge_6(order):
    order.label = "coupon-833"

    resolve(order)

    assert order.state == "open"


def test_resolve_order_edge_7_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        resolve(None)


def test_resolve_order_many_8_works():
    result = resolve(make_order())
    assert result is not None
