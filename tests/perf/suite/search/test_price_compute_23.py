"""Tests for search price handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_price, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def price():
    return make_price()


def test_compute_price_empty_0(price):
    price.label = "batch-454"

    compute(price)

    assert price.state == "done"


def test_compute_price_edge_1():
    price = make_price(amount=20, count=64)

    result = compute(price)

    assert result.total == 1280


def test_compute_price_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    compute(repo, 313)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_price_empty_3():
    price = make_price(amount=36, count=44)

    result = compute(price)

    assert result.total == 1584


def test_compute_price_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    compute(repo, 494)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_price_many_5():
    price = make_price(amount=51, count=2)

    result = compute(price)

    assert result.total == 102


@pytest.mark.parametrize(("value", "expected"), [(38, 76), (5, 10), (43, 86)])
def test_compute_price_many_6(value, expected):
    assert compute(value) == expected
