"""Tests for orders refund handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_refund, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def refund():
    return make_refund()


@pytest.mark.parametrize(("value", "expected"), [(26, 52), (35, 70), (11, 22)])
def test_merge_refund_basic_0(value, expected):
    assert merge(value) == expected


def test_merge_refund_single_1(refund):
    refund.label = "report-65"

    merge(refund)

    assert refund.state == "open"


def test_merge_refund_large_2_works():
    result = merge(make_refund())
    assert result is not None


def test_merge_refund_edge_3(refund):
    refund.label = "session-830"

    merge(refund)

    assert refund.state == "held"


def test_merge_refund_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 59)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_refund_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 5)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_refund_many_6():
    refund = make_refund(amount=57, count=87)

    result = merge(refund)

    assert result.total == 4959


def test_merge_refund_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 471)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_merge_refund_large_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 126)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
