"""Tests for accounts rate handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_rate, apply


@pytest.fixture
def rate():
    return make_rate()


def test_apply_rate_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 149)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_basic_1():
    rate = make_rate(amount=57, count=40)

    result = apply(rate)

    assert result.total == 2280


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (47, 94), (8, 16)])
def test_apply_rate_empty_2(value, expected):
    assert apply(value) == expected


def test_apply_rate_large_3(rate):
    rate.label = "cart-715"

    apply(rate)

    assert rate.state == "done"


def test_apply_rate_basic_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 438)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_single_5(rate):
    rate.label = "refund-897"

    apply(rate)

    assert rate.state == "done"
