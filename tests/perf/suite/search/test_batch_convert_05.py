"""Tests for search batch handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_batch, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_convert_batch_empty_0():
    batch = make_batch(amount=81, count=39)

    result = convert(batch)

    assert result.total == 3159


def test_convert_batch_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    convert(repo, 115)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_batch_empty_2_works():
    result = convert(make_batch())
    assert result is not None


def test_convert_batch_edge_3():
    batch = make_batch(amount=47, count=16)

    result = convert(batch)

    assert result.total == 752


def test_convert_batch_single_4(batch):
    batch.label = "token-161"

    convert(batch)

    assert batch.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (12, 24), (31, 62)])
def test_convert_batch_empty_5(value, expected):
    assert convert(value) == expected


def test_convert_batch_empty_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    convert(repo, 467)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_batch_single_7():
    batch = make_batch(amount=86, count=17)

    result = convert(batch)

    assert result.total == 1462


def test_convert_batch_edge_8():
    batch = make_batch(amount=28, count=72)

    result = convert(batch)

    assert result.total == 2016


def test_convert_batch_large_9():
    batch = make_batch(amount=19, count=54)

    result = convert(batch)

    assert result.total == 1026
