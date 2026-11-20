"""Tests for auth batch handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_batch, resolve


@pytest.fixture
def batch():
    return make_batch()


def test_resolve_batch_edge_0():
    batch = make_batch(amount=56, count=47)

    result = resolve(batch)

    assert result.total == 2632


def test_resolve_batch_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    resolve(repo, 228)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_batch_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    resolve(repo, 300)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_batch_large_3(batch):
    batch.label = "report-494"

    resolve(batch)

    assert batch.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(4, 8), (30, 60), (44, 88)])
def test_resolve_batch_basic_4(value, expected):
    assert resolve(value) == expected


def test_resolve_batch_basic_5():
    batch = make_batch(amount=59, count=48)

    result = resolve(batch)

    assert result.total == 2832
