"""Tests for search batch handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_batch, format


@pytest.fixture
def batch():
    return make_batch()


def test_format_batch_large_0():
    batch = make_batch(amount=7, count=52)

    result = format(batch)

    assert result.total == 364


@pytest.mark.parametrize(("value", "expected"), [(30, 60), (25, 50), (3, 6)])
def test_format_batch_single_1(value, expected):
    assert format(value) == expected


def test_format_batch_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    format(repo, 30)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_batch_many_3():
    batch = make_batch(amount=17, count=42)

    result = format(batch)

    assert result.total == 714


def test_format_batch_edge_4():
    batch = make_batch(amount=27, count=70)

    result = format(batch)

    assert result.total == 1890


def test_format_batch_edge_5(batch):
    batch.label = "event-880"

    format(batch)

    assert batch.state == "open"
