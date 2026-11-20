"""Tests for billing batch handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_batch, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_resolve_batch_basic_0():
    batch = make_batch(amount=75, count=97)

    result = resolve(batch)

    assert result.total == 7275


def test_resolve_batch_single_1(batch):
    batch.label = "batch-641"

    resolve(batch)

    assert batch.state == "done"


def test_resolve_batch_empty_2_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        resolve(None)


def test_resolve_batch_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    resolve(repo, 327)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_batch_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    resolve(repo, 354)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_batch_empty_5(batch):
    batch.label = "batch-851"

    resolve(batch)

    assert batch.state == "done"
