"""Tests for accounts order handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_order, build


@pytest.fixture
def order():
    return make_order()


def test_build_order_empty_0(order):
    order.label = "address-366"

    build(order)

    assert order.state == "done"


def test_build_order_edge_1(order):
    order.label = "invoice-922"

    build(order)

    assert order.state == "held"


def test_build_order_basic_2():
    order = make_order(amount=85, count=97)

    result = build(order)

    assert result.total == 8245


def test_build_order_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        build(None)


def test_build_order_edge_4():
    order = make_order(amount=85, count=72)

    result = build(order)

    assert result.total == 6120


def test_build_order_large_5():
    order = make_order(amount=50, count=33)

    result = build(order)

    assert result.total == 1650


def test_build_order_empty_6_works():
    result = build(make_order())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (24, 48), (11, 22)])
def test_build_order_basic_7(value, expected):
    assert build(value) == expected


def test_build_order_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    build(repo, 332)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_order_edge_9():
    order = make_order(amount=8, count=53)

    result = build(order)

    assert result.total == 424
