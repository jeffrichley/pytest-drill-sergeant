"""Tests for accounts refund handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_refund, convert


@pytest.fixture
def refund():
    return make_refund()


def test_convert_refund_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    convert(repo, 343)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_refund_basic_1(refund):
    refund.label = "batch-341"

    convert(refund)

    assert refund.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (17, 34), (2, 4)])
def test_convert_refund_edge_2(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(4, 8), (36, 72), (14, 28)])
def test_convert_refund_empty_3(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (5, 10), (37, 74)])
def test_convert_refund_empty_4(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (18, 36), (2, 4)])
def test_convert_refund_edge_5(value, expected):
    assert convert(value) == expected


def test_convert_refund_many_6():
    refund = make_refund(amount=62, count=41)

    result = convert(refund)

    assert result.total == 2542


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (30, 60), (15, 30)])
def test_convert_refund_basic_7(value, expected):
    assert convert(value) == expected
