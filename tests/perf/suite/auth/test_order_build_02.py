"""Tests for auth order handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_order, build

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_build_order_edge_0(order):
    order.label = "price-168"

    build(order)

    assert order.state == "done"


def test_build_order_single_1(order):
    order.label = "cart-483"

    build(order)

    assert order.state == "done"


def test_build_order_edge_2(order):
    order.label = "batch-600"

    build(order)

    assert order.state == "held"


def test_build_order_basic_3():
    order = make_order(amount=62, count=31)

    result = build(order)

    assert result.total == 1922


def test_build_order_single_4():
    order = make_order(amount=43, count=1)

    result = build(order)

    assert result.total == 43


def test_build_order_edge_5_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)


def test_build_order_many_6(order):
    order.label = "session-542"

    build(order)

    assert order.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (40, 80), (18, 36)])
def test_build_order_many_7(value, expected):
    assert build(value) == expected


def test_build_order_many_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    build(repo, 250)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
