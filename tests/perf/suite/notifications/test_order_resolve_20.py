"""Tests for notifications order handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_order, resolve


@pytest.fixture
def order():
    return make_order()


def test_resolve_order_many_0():
    order = make_order(amount=68, count=97)

    result = resolve(order)

    assert result.total == 6596


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (4, 8), (43, 86)])
def test_resolve_order_empty_1(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (12, 24), (29, 58)])
def test_resolve_order_empty_2(value, expected):
    assert resolve(value) == expected


def test_resolve_order_edge_3_runs():
    resolve(make_order())


@pytest.mark.parametrize(("value", "expected"), [(22, 44), (25, 50), (29, 58)])
def test_resolve_order_edge_4(value, expected):
    assert resolve(value) == expected
