"""Tests for inventory refund handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_refund, resolve


@pytest.fixture
def refund():
    return make_refund()


def test_resolve_refund_empty_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    resolve(repo, 204)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (5, 10), (7, 14)])
def test_resolve_refund_edge_1(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (4, 8), (41, 82)])
def test_resolve_refund_basic_2(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (41, 82), (16, 32)])
def test_resolve_refund_empty_3(value, expected):
    assert resolve(value) == expected


def test_resolve_refund_edge_4(refund):
    refund.label = "session-776"

    resolve(refund)

    assert refund.state == "done"


def test_resolve_refund_large_5():
    refund = make_refund(amount=80, count=41)

    result = resolve(refund)

    assert result.total == 3280


def test_resolve_refund_single_6():
    refund = make_refund(amount=80, count=22)

    result = resolve(refund)

    assert result.total == 1760


@pytest.mark.parametrize(("value", "expected"), [(43, 86), (5, 10), (19, 38)])
def test_resolve_refund_single_7(value, expected):
    assert resolve(value) == expected
