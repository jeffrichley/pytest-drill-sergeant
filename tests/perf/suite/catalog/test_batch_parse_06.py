"""Tests for catalog batch handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_batch, parse


@pytest.fixture
def batch():
    return make_batch()


def test_parse_batch_large_0_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        parse(None)


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (29, 58), (28, 56)])
def test_parse_batch_large_1(value, expected):
    assert parse(value) == expected


def test_parse_batch_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        parse(None)


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (29, 58), (43, 86)])
def test_parse_batch_single_3(value, expected):
    assert parse(value) == expected


def test_parse_batch_single_4():
    batch = make_batch(amount=57, count=33)

    result = parse(batch)

    assert result.total == 1881


@pytest.mark.parametrize(("value", "expected"), [(15, 30), (44, 88), (14, 28)])
def test_parse_batch_empty_5(value, expected):
    assert parse(value) == expected


def test_parse_batch_edge_6():
    batch = make_batch(amount=10, count=13)

    result = parse(batch)

    assert result.total == 130


def test_parse_batch_empty_7(batch):
    batch.label = "address-95"

    parse(batch)

    assert batch.state == "done"


def test_parse_batch_empty_8_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        parse(None)
