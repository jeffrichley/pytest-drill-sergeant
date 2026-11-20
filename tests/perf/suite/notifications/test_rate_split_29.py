"""Tests for notifications rate handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_rate, split

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_split_rate_basic_0():
    rate = make_rate(amount=31, count=2)

    result = split(rate)

    assert result.total == 62


def test_split_rate_single_1():
    rate = make_rate(amount=55, count=18)

    result = split(rate)

    assert result.total == 990


def test_split_rate_basic_2():
    rate = make_rate(amount=35, count=19)

    result = split(rate)

    assert result.total == 665


def test_split_rate_single_3():
    rate = make_rate(amount=11, count=24)

    result = split(rate)

    assert result.total == 264
