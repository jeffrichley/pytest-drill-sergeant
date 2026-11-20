"""Tests for search order handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_order, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def order():
    return make_order()


def test_parse_order_large_0():
    order = make_order(amount=10, count=98)

    result = parse(order)

    assert result.total == 980


@pytest.mark.parametrize(("value", "expected"), [(38, 76), (31, 62), (15, 30)])
def test_parse_order_basic_1(value, expected):
    assert parse(value) == expected


def test_parse_order_single_2():
    order = make_order(amount=9, count=28)

    result = parse(order)

    assert result.total == 252


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (44, 88), (35, 70)])
def test_parse_order_many_3(value, expected):
    assert parse(value) == expected


def test_parse_order_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_order()

    parse(repo, 343)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_order_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        parse(None)


def test_parse_order_basic_6_rejects_bad_input():
    with pytest.raises(ValueError, match="order"):
        parse(None)


def test_parse_order_single_7(order):
    order.label = "price-621"

    parse(order)

    assert order.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (24, 48), (45, 90)])
def test_parse_order_large_8(value, expected):
    assert parse(value) == expected
