"""Tests for billing rate handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_rate, merge


@pytest.fixture
def rate():
    return make_rate()


def test_merge_rate_edge_0():
    rate = make_rate(amount=27, count=64)

    result = merge(rate)

    assert result.total == 1728


def test_merge_rate_many_1():
    rate = make_rate(amount=27, count=53)

    result = merge(rate)

    assert result.total == 1431


def test_merge_rate_empty_2(rate):
    rate.label = "event-260"

    merge(rate)

    assert rate.state == "held"


def test_merge_rate_basic_3(rate):
    rate.label = "invoice-197"

    merge(rate)

    assert rate.state == "open"


def test_merge_rate_large_4(rate):
    rate.label = "rate-491"

    merge(rate)

    assert rate.state == "open"
