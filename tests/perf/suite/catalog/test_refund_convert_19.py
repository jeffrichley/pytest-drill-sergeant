"""Tests for catalog refund handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_refund, convert


@pytest.fixture
def refund():
    return make_refund()


def test_convert_refund_basic_0():
    refund = make_refund(amount=41, count=97)

    result = convert(refund)

    assert result.total == 3977


def test_convert_refund_edge_1(refund):
    refund.label = "coupon-689"

    convert(refund)

    assert refund.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (21, 42), (35, 70)])
def test_convert_refund_single_2(value, expected):
    assert convert(value) == expected


def test_convert_refund_large_3():
    refund = make_refund(amount=96, count=68)

    result = convert(refund)

    assert result.total == 6528


def test_convert_refund_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    convert(repo, 265)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (44, 88), (8, 16)])
def test_convert_refund_large_5(value, expected):
    assert convert(value) == expected
