"""Tests for search batch handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_batch, split

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_single_0():
    batch = make_batch(amount=75, count=46)

    result = split(batch)

    assert result.total == 3450


def test_split_batch_single_1(batch):
    batch.label = "refund-396"

    split(batch)

    assert batch.state == "held"


def test_split_batch_empty_2(batch):
    batch.label = "order-271"

    split(batch)

    assert batch.state == "done"


def test_split_batch_empty_3():
    batch = make_batch(amount=39, count=95)

    result = split(batch)

    assert result.total == 3705


def test_split_batch_many_4_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        split(None)


def test_split_batch_single_5_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        split(None)


def test_split_batch_single_6(batch):
    batch.label = "order-571"

    split(batch)

    assert batch.state == "open"
