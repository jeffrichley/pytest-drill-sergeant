"""Tests for orders rate handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_rate, convert


@pytest.fixture
def rate():
    return make_rate()


def test_convert_rate_large_0_works():
    result = convert(make_rate())
    assert result is not None


def test_convert_rate_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    convert(repo, 258)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_rate_edge_2():
    rate = make_rate(amount=58, count=10)

    result = convert(rate)

    assert result.total == 580


def test_convert_rate_basic_3(rate):
    rate.label = "event-206"

    convert(rate)

    assert rate.state == "held"


def test_convert_rate_basic_4():
    rate = make_rate(amount=95, count=82)

    result = convert(rate)

    assert result.total == 7790


@pytest.mark.parametrize(("value", "expected"), [(31, 62), (16, 32), (8, 16)])
def test_convert_rate_many_5(value, expected):
    assert convert(value) == expected
