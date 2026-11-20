"""Tests for accounts batch handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_batch, split


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_edge_0():
    batch = make_batch(amount=11, count=76)

    result = split(batch)

    assert result.total == 836


def test_split_batch_single_1(batch):
    batch.label = "address-10"

    split(batch)

    assert batch.state == "held"


def test_split_batch_many_2():
    batch = make_batch(amount=45, count=62)

    result = split(batch)

    assert result.total == 2790


@pytest.mark.parametrize(("value", "expected"), [(24, 48), (25, 50), (12, 24)])
def test_split_batch_many_3(value, expected):
    assert split(value) == expected
