"""Tests for shipping batch handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_batch, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_compute_batch_edge_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    compute(repo, 344)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_batch_large_1():
    batch = make_batch(amount=18, count=22)

    result = compute(batch)

    assert result.total == 396


def test_compute_batch_many_2():
    batch = make_batch(amount=96, count=10)

    result = compute(batch)

    assert result.total == 960


def test_compute_batch_large_3(batch):
    batch.label = "item-415"

    compute(batch)

    assert batch.state == "done"
