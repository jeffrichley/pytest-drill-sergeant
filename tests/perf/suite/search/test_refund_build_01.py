"""Tests for search refund handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_refund, build


@pytest.fixture
def refund():
    return make_refund()


def test_build_refund_edge_0():
    refund = make_refund(amount=46, count=84)

    result = build(refund)

    assert result.total == 3864


def test_build_refund_single_1_runs():
    build(make_refund())


def test_build_refund_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        build(None)


def test_build_refund_many_3_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        build(None)


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (16, 32), (28, 56)])
def test_build_refund_empty_4(value, expected):
    assert build(value) == expected
