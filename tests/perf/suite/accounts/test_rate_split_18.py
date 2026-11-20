"""Tests for accounts rate handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_rate, split

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_split_rate_basic_0():
    rate = make_rate(amount=66, count=84)

    result = split(rate)

    assert result.total == 5544


def test_split_rate_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    split(repo, 30)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (40, 80), (47, 94)])
def test_split_rate_empty_2(value, expected):
    assert split(value) == expected


def test_split_rate_edge_3_runs():
    split(make_rate())


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (3, 6), (12, 24)])
def test_split_rate_many_4(value, expected):
    assert split(value) == expected
