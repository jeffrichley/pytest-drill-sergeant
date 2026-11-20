"""Tests for auth rate handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_rate, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_merge_rate_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    merge(repo, 238)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_rate_edge_1():
    rate = make_rate(amount=27, count=41)

    result = merge(rate)

    assert result.total == 1107


def test_merge_rate_empty_2():
    rate = make_rate(amount=64, count=31)

    result = merge(rate)

    assert result.total == 1984


def test_merge_rate_edge_3():
    rate = make_rate(amount=75, count=39)

    result = merge(rate)

    assert result.total == 2925
