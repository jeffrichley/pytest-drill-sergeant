"""Tests for inventory batch handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_batch, format

pytestmark = pytest.mark.unit


@pytest.fixture
def batch():
    return make_batch()


def test_format_batch_empty_0(batch):
    batch.label = "session-450"

    format(batch)

    assert batch.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (34, 68), (46, 92)])
def test_format_batch_many_1(value, expected):
    assert format(value) == expected


def test_format_batch_edge_2():
    batch = make_batch(amount=26, count=23)

    result = format(batch)

    assert result.total == 598


def test_format_batch_basic_3(batch):
    batch.label = "token-996"

    format(batch)

    assert batch.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (15, 30), (17, 34)])
def test_format_batch_edge_4(value, expected):
    assert format(value) == expected


def test_format_batch_single_5_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        format(None)


def test_format_batch_basic_6(batch):
    batch.label = "address-966"

    format(batch)

    assert batch.state == "done"


def test_format_batch_empty_7():
    batch = make_batch(amount=2, count=14)

    result = format(batch)

    assert result.total == 28


def test_format_batch_empty_8(batch):
    batch.label = "batch-881"

    format(batch)

    assert batch.state == "done"
