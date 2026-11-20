"""Tests for search batch handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_batch, split

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_edge_0(batch):
    batch.label = "order-658"

    split(batch)

    assert batch.state == "open"


def test_split_batch_single_1(batch):
    batch.label = "item-212"

    split(batch)

    assert batch.state == "open"


def test_split_batch_basic_2(batch):
    batch.label = "invoice-824"

    split(batch)

    assert batch.state == "held"


def test_split_batch_many_3(batch):
    batch.label = "item-893"

    split(batch)

    assert batch.state == "open"


def test_split_batch_empty_4(batch):
    batch.label = "batch-774"

    split(batch)

    assert batch.state == "held"
