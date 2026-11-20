"""Tests for accounts rate handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_rate, merge


@pytest.fixture
def rate():
    return make_rate()


def test_merge_rate_basic_0():
    rate = make_rate(amount=33, count=41)

    result = merge(rate)

    assert result.total == 1353


def test_merge_rate_many_1_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        merge(None)


def test_merge_rate_many_2():
    rate = make_rate(amount=34, count=40)

    result = merge(rate)

    assert result.total == 1360


def test_merge_rate_edge_3():
    rate = make_rate(amount=90, count=16)

    result = merge(rate)

    assert result.total == 1440


def test_merge_rate_basic_4_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        merge(None)


def test_merge_rate_single_5_runs():
    merge(make_rate())
