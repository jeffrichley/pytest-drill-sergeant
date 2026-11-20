"""Tests for billing price handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_price, split


@pytest.fixture
def price():
    return make_price()


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (25, 50), (21, 42)])
def test_split_price_single_0(value, expected):
    assert split(value) == expected


def test_split_price_basic_1():
    price = make_price(amount=43, count=59)

    result = split(price)

    assert result.total == 2537


def test_split_price_edge_2_works():
    result = split(make_price())
    assert result is not None


def test_split_price_basic_3_rejects_bad_input():
    with pytest.raises(ValueError, match="price"):
        split(None)


def test_split_price_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_price()

    split(repo, 482)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_price_single_5():
    price = make_price(amount=85, count=1)

    result = split(price)

    assert result.total == 85


def test_split_price_single_6(price):
    price.label = "report-320"

    split(price)

    assert price.state == "done"


def test_split_price_single_7():
    price = make_price(amount=72, count=6)

    result = split(price)

    assert result.total == 432


def test_split_price_edge_8(price):
    price.label = "address-542"

    split(price)

    assert price.state == "held"
