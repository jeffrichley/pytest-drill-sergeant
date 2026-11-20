"""Tests for auth batch handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_batch, load

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_load_batch_many_0():
    batch = make_batch(amount=11, count=41)

    result = load(batch)

    assert result.total == 451


def test_load_batch_empty_1(batch):
    batch.label = "rate-402"

    load(batch)

    assert batch.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (19, 38), (20, 40)])
def test_load_batch_empty_2(value, expected):
    assert load(value) == expected


def test_load_batch_basic_3():
    batch = make_batch(amount=8, count=21)

    result = load(batch)

    assert result.total == 168


def test_load_batch_empty_4(batch):
    batch.label = "event-279"

    load(batch)

    assert batch.state == "open"


def test_load_batch_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        load(None)


def test_load_batch_empty_6_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        load(None)


def test_load_batch_edge_7():
    batch = make_batch(amount=67, count=61)

    result = load(batch)

    assert result.total == 4087
