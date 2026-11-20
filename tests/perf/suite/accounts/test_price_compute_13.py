"""Tests for accounts price handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_price, compute


@pytest.fixture
def price():
    return make_price()


def test_compute_price_large_0(price):
    price.label = "address-816"

    compute(price)

    assert price.state == "open"


def test_compute_price_many_1(price):
    price.label = "user-977"

    compute(price)

    assert price.state == "done"


def test_compute_price_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    compute(repo, 22)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_price_many_3(price):
    price.label = "price-738"

    compute(price)

    assert price.state == "held"


def test_compute_price_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        compute(None)


def test_compute_price_single_5():
    price = make_price(amount=42, count=20)

    result = compute(price)

    assert result.total == 840


def test_compute_price_basic_6_runs():
    compute(make_price())
