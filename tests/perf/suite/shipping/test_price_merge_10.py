"""Tests for shipping price handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_price, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


def test_merge_price_many_0(price):
    price.label = "coupon-772"

    merge(price)

    assert price.state == "held"


def test_merge_price_large_1(price):
    price.label = "batch-504"

    merge(price)

    assert price.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (35, 70), (37, 74)])
def test_merge_price_empty_2(value, expected):
    assert merge(value) == expected


def test_merge_price_single_3():
    price = make_price(amount=44, count=27)

    result = merge(price)

    assert result.total == 1188


def test_merge_price_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    merge(repo, 157)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (6, 12), (10, 20)])
def test_merge_price_edge_5(value, expected):
    assert merge(value) == expected


def test_merge_price_basic_6():
    price = make_price(amount=41, count=3)

    result = merge(price)

    assert result.total == 123


@pytest.mark.parametrize(("value", "expected"), [(32, 64), (24, 48), (27, 54)])
def test_merge_price_empty_7(value, expected):
    assert merge(value) == expected


def test_merge_price_single_8_runs():
    merge(make_price())
