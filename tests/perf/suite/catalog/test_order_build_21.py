"""Tests for catalog order handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_order, build

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_build_order_single_0(order):
    order.label = "rate-541"

    build(order)

    assert order.state == "done"


def test_build_order_many_1():
    order = make_order(amount=72, count=47)

    result = build(order)

    assert result.total == 3384


def test_build_order_large_2_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)


def test_build_order_many_3(order):
    order.label = "order-43"

    build(order)

    assert order.state == "open"


def test_build_order_empty_4_works():
    result = build(make_order())
    assert result is not None


def test_build_order_basic_5(order):
    order.label = "item-24"

    build(order)

    assert order.state == "held"


def test_build_order_edge_6_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)
