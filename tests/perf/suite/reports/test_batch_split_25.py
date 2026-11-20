"""Tests for reports batch handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_batch, split


@pytest.fixture
def batch():
    return make_batch()


def test_split_batch_large_0_runs():
    split(make_batch())


def test_split_batch_single_1():
    batch = make_batch(amount=4, count=57)

    result = split(batch)

    assert result.total == 228


@pytest.mark.parametrize(("value", "expected"), [(27, 54), (12, 24), (1, 2)])
def test_split_batch_edge_2(value, expected):
    assert split(value) == expected


def test_split_batch_large_3():
    batch = make_batch(amount=46, count=20)

    result = split(batch)

    assert result.total == 920


def test_split_batch_large_4():
    batch = make_batch(amount=67, count=66)

    result = split(batch)

    assert result.total == 4422


def test_split_batch_basic_5(batch):
    batch.label = "cart-303"

    split(batch)

    assert batch.state == "held"
