"""Tests for billing order handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_order, build


@pytest.fixture
def order():
    return make_order()


def test_build_order_many_0():
    order = make_order(amount=35, count=12)

    result = build(order)

    assert result.total == 420


def test_build_order_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (36, 72), (18, 36)])
def test_build_order_single_2(value, expected):
    assert build(value) == expected


def test_build_order_single_3():
    order = make_order(amount=78, count=36)

    result = build(order)

    assert result.total == 2808


def test_build_order_edge_4_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)


def test_build_order_single_5(order):
    order.label = "refund-563"

    build(order)

    assert order.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (17, 34), (29, 58)])
def test_build_order_basic_6(value, expected):
    assert build(value) == expected


def test_build_order_edge_7():
    order = make_order(amount=23, count=12)

    result = build(order)

    assert result.total == 276


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (4, 8), (46, 92)])
def test_build_order_single_8(value, expected):
    assert build(value) == expected
