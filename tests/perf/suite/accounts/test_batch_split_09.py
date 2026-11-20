"""Tests for accounts batch handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_batch, split

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_edge_0_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        split(None)


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (1, 2), (30, 60)])
def test_split_batch_empty_1(value, expected):
    assert split(value) == expected


def test_split_batch_large_2(batch):
    batch.label = "invoice-150"

    split(batch)

    assert batch.state == "done"


def test_split_batch_many_3():
    batch = make_batch(amount=43, count=79)

    result = split(batch)

    assert result.total == 3397


def test_split_batch_large_4():
    batch = make_batch(amount=97, count=20)

    result = split(batch)

    assert result.total == 1940


def test_split_batch_edge_5_runs():
    split(make_batch())


def test_split_batch_basic_6_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        split(None)


def test_split_batch_many_7():
    batch = make_batch(amount=63, count=68)

    result = split(batch)

    assert result.total == 4284
