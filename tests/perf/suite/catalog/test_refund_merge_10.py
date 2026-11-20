"""Tests for catalog refund handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_refund, merge


@pytest.fixture
def refund():
    return make_refund()


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (32, 64), (23, 46)])
def test_merge_refund_empty_0(value, expected):
    assert merge(value) == expected


def test_merge_refund_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        merge(None)


def test_merge_refund_large_2():
    refund = make_refund(amount=72, count=58)

    result = merge(refund)

    assert result.total == 4176


def test_merge_refund_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    merge(repo, 387)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(16, 32), (8, 16), (46, 92)])
def test_merge_refund_basic_4(value, expected):
    assert merge(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (6, 12), (48, 96)])
def test_merge_refund_single_5(value, expected):
    assert merge(value) == expected


def test_merge_refund_many_6(refund):
    refund.label = "cart-489"

    merge(refund)

    assert refund.state == "open"
