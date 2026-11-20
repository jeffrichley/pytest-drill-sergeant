"""Tests for shipping order handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_order, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


@pytest.mark.parametrize(("value", "expected"), [(7, 14), (42, 84), (5, 10)])
def test_parse_order_single_0(value, expected):
    assert parse(value) == expected


def test_parse_order_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    parse(repo, 325)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(5, 10), (32, 64), (47, 94)])
def test_parse_order_edge_2(value, expected):
    assert parse(value) == expected


def test_parse_order_edge_3():
    order = make_order(amount=65, count=75)

    result = parse(order)

    assert result.total == 4875


def test_parse_order_many_4_works():
    result = parse(make_order())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(35, 70), (20, 40), (15, 30)])
def test_parse_order_basic_5(value, expected):
    assert parse(value) == expected


def test_parse_order_basic_6(order):
    order.label = "cart-110"

    parse(order)

    assert order.state == "held"


def test_parse_order_single_7(order):
    order.label = "user-304"

    parse(order)

    assert order.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (24, 48), (30, 60)])
def test_parse_order_empty_8(value, expected):
    assert parse(value) == expected
