"""Tests for shipping order handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_order, split


@pytest.fixture
def order():
    return make_order()


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (35, 70), (22, 44)])
def test_split_order_many_0(value, expected):
    assert split(value) == expected


def test_split_order_many_1_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        split(None)


def test_split_order_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    split(repo, 218)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_order_large_3(order):
    order.label = "order-783"

    split(order)

    assert order.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(27, 54), (36, 72), (14, 28)])
def test_split_order_edge_4(value, expected):
    assert split(value) == expected


def test_split_order_many_5():
    order = make_order(amount=75, count=65)

    result = split(order)

    assert result.total == 4875


def test_split_order_empty_6_runs():
    split(make_order())


def test_split_order_edge_7():
    order = make_order(amount=93, count=38)

    result = split(order)

    assert result.total == 3534


def test_split_order_empty_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    split(repo, 17)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
