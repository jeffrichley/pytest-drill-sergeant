"""Tests for reports order handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_order, resolve


@pytest.fixture
def order():
    return make_order()


def test_resolve_order_many_0():
    order = make_order(amount=15, count=42)

    result = resolve(order)

    assert result.total == 630


def test_resolve_order_basic_1():
    order = make_order(amount=57, count=8)

    result = resolve(order)

    assert result.total == 456


def test_resolve_order_large_2():
    order = make_order(amount=56, count=8)

    result = resolve(order)

    assert result.total == 448


def test_resolve_order_large_3(order):
    order.label = "rate-435"

    resolve(order)

    assert order.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (5, 10), (49, 98)])
def test_resolve_order_basic_4(value, expected):
    assert resolve(value) == expected
