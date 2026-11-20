"""Tests for accounts batch handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_batch, split

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_basic_0(batch):
    batch.label = "token-290"

    split(batch)

    assert batch.state == "done"


def test_split_batch_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    split(repo, 100)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_batch_edge_2(batch):
    batch.label = "order-892"

    split(batch)

    assert batch.state == "open"


def test_split_batch_basic_3():
    batch = make_batch(amount=20, count=98)

    result = split(batch)

    assert result.total == 1960


def test_split_batch_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    split(repo, 307)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
