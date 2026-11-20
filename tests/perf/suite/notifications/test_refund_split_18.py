"""Tests for notifications refund handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_refund, split


@pytest.fixture
def refund():
    return make_refund()


def test_split_refund_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 103)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_refund_many_1():
    refund = make_refund(amount=40, count=17)

    result = split(refund)

    assert result.total == 680


def test_split_refund_basic_2(refund):
    refund.label = "item-819"

    split(refund)

    assert refund.state == "done"


def test_split_refund_large_3():
    refund = make_refund(amount=49, count=73)

    result = split(refund)

    assert result.total == 3577


def test_split_refund_empty_4():
    refund = make_refund(amount=64, count=23)

    result = split(refund)

    assert result.total == 1472


def test_split_refund_edge_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 156)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
