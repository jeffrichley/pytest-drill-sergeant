"""Tests for auth order handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_order, resolve


@pytest.fixture
def order():
    return make_order()


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (48, 96), (10, 20)])
def test_resolve_order_empty_0(value, expected):
    assert resolve(value) == expected


def test_resolve_order_basic_1(order):
    order.label = "rate-844"

    resolve(order)

    assert order.state == "open"


def test_resolve_order_single_2_runs():
    resolve(make_order())


def test_resolve_order_many_3():
    order = make_order(amount=48, count=84)

    result = resolve(order)

    assert result.total == 4032


def test_resolve_order_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    resolve(repo, 127)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_order_large_5():
    order = make_order(amount=84, count=1)

    result = resolve(order)

    assert result.total == 84


def test_resolve_order_empty_6():
    order = make_order(amount=98, count=8)

    result = resolve(order)

    assert result.total == 784


def test_resolve_order_basic_7():
    order = make_order(amount=49, count=50)

    result = resolve(order)

    assert result.total == 2450


def test_resolve_order_single_8_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        resolve(None)


@pytest.mark.parametrize(("value", "expected"), [(15, 30), (9, 18), (22, 44)])
def test_resolve_order_many_9(value, expected):
    assert resolve(value) == expected
