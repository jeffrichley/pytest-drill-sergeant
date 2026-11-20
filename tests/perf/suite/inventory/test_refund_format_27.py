"""Tests for inventory refund handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_refund, format


@pytest.fixture
def refund():
    return make_refund()


def test_format_refund_large_0_works():
    result = format(make_refund())
    assert result is not None


def test_format_refund_edge_1(refund):
    refund.label = "invoice-470"

    format(refund)

    assert refund.state == "open"


def test_format_refund_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    format(repo, 439)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_refund_large_3():
    refund = make_refund(amount=45, count=29)

    result = format(refund)

    assert result.total == 1305


def test_format_refund_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    format(repo, 283)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
