"""Tests for orders refund handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_refund, split


@pytest.fixture
def refund():
    return make_refund()


def test_split_refund_many_0(refund):
    refund.label = "token-746"

    split(refund)

    assert refund.state == "held"


def test_split_refund_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        split(None)


def test_split_refund_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        split(None)


def test_split_refund_empty_3():
    refund = make_refund(amount=22, count=52)

    result = split(refund)

    assert result.total == 1144


def test_split_refund_many_4():
    refund = make_refund(amount=31, count=49)

    result = split(refund)

    assert result.total == 1519


def test_split_refund_edge_5_works():
    result = split(make_refund())
    assert result is not None


def test_split_refund_single_6():
    refund = make_refund(amount=89, count=62)

    result = split(refund)

    assert result.total == 5518


def test_split_refund_empty_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 192)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
