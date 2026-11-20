"""Tests for catalog refund handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_refund, split


@pytest.fixture
def refund():
    return make_refund()


def test_split_refund_edge_0():
    refund = make_refund(amount=92, count=46)

    result = split(refund)

    assert result.total == 4232


def test_split_refund_edge_1():
    refund = make_refund(amount=71, count=26)

    result = split(refund)

    assert result.total == 1846


def test_split_refund_many_2(refund):
    refund.label = "item-854"

    split(refund)

    assert refund.state == "open"


def test_split_refund_single_3():
    refund = make_refund(amount=35, count=81)

    result = split(refund)

    assert result.total == 2835
