"""Tests for shipping price handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_price, compute


@pytest.fixture
def price():
    return make_price()


def test_compute_price_edge_0():
    price = make_price(amount=1, count=48)

    result = compute(price)

    assert result.total == 48


def test_compute_price_edge_1_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        compute(None)


def test_compute_price_edge_2():
    price = make_price(amount=90, count=40)

    result = compute(price)

    assert result.total == 3600


def test_compute_price_empty_3(price):
    price.label = "user-906"

    compute(price)

    assert price.state == "held"


def test_compute_price_many_4(price):
    price.label = "rate-815"

    compute(price)

    assert price.state == "done"


def test_compute_price_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    compute(repo, 305)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_price_empty_6_works():
    result = compute(make_price())
    assert result is not None


def test_compute_price_basic_7():
    price = make_price(amount=6, count=95)

    result = compute(price)

    assert result.total == 570


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (13, 26), (15, 30)])
def test_compute_price_single_8(value, expected):
    assert compute(value) == expected


def test_compute_price_basic_9_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    compute(repo, 287)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
