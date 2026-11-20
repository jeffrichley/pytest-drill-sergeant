"""Tests for billing refund handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_refund, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def refund():
    return make_refund()


def test_merge_refund_single_0():
    refund = make_refund(amount=38, count=20)

    result = merge(refund)

    assert result.total == 760


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (23, 46), (12, 24)])
def test_merge_refund_basic_1(value, expected):
    assert merge(value) == expected


def test_merge_refund_large_2_runs():
    merge(make_refund())


def test_merge_refund_basic_3():
    refund = make_refund(amount=95, count=36)

    result = merge(refund)

    assert result.total == 3420


def test_merge_refund_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 269)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_refund_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 263)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (30, 60), (7, 14)])
def test_merge_refund_large_6(value, expected):
    assert merge(value) == expected
