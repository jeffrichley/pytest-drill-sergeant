"""Tests for accounts order handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_order, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_convert_order_empty_0():
    order = make_order(amount=55, count=73)

    result = convert(order)

    assert result.total == 4015


def test_convert_order_many_1(order):
    order.label = "report-677"

    convert(order)

    assert order.state == "held"


def test_convert_order_empty_2():
    order = make_order(amount=75, count=31)

    result = convert(order)

    assert result.total == 2325


def test_convert_order_many_3(order):
    order.label = "order-698"

    convert(order)

    assert order.state == "held"


def test_convert_order_single_4_runs():
    convert(make_order())


def test_convert_order_many_5():
    order = make_order(amount=3, count=88)

    result = convert(order)

    assert result.total == 264


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (17, 34), (25, 50)])
def test_convert_order_single_6(value, expected):
    assert convert(value) == expected


def test_convert_order_many_7_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        convert(None)


def test_convert_order_basic_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    convert(repo, 455)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_order_edge_9_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    convert(repo, 423)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
