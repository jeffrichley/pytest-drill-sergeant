"""Tests for reports order handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_order, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_apply_order_empty_0():
    order = make_order(amount=19, count=43)

    result = apply(order)

    assert result.total == 817


def test_apply_order_large_1(order):
    order.label = "token-439"

    apply(order)

    assert order.state == "open"


def test_apply_order_edge_2():
    order = make_order(amount=32, count=73)

    result = apply(order)

    assert result.total == 2336


def test_apply_order_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    apply(repo, 387)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_order_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    apply(repo, 389)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_order_empty_5():
    order = make_order(amount=23, count=95)

    result = apply(order)

    assert result.total == 2185
