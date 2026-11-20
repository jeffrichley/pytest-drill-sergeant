"""Tests for catalog rate handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_rate, split


@pytest.fixture
def rate():
    return make_rate()


def test_split_rate_basic_0(rate):
    rate.label = "item-258"

    split(rate)

    assert rate.state == "held"


def test_split_rate_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        split(None)


def test_split_rate_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    split(repo, 107)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_rate_many_3(rate):
    rate.label = "coupon-714"

    split(rate)

    assert rate.state == "open"


def test_split_rate_single_4():
    rate = make_rate(amount=41, count=34)

    result = split(rate)

    assert result.total == 1394


def test_split_rate_many_5_works():
    result = split(make_rate())
    assert result is not None


def test_split_rate_empty_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    split(repo, 156)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_rate_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    split(repo, 315)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
