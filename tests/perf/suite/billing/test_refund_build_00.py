"""Tests for billing refund handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_refund, build

pytestmark = pytest.mark.unit


@pytest.fixture
def refund():
    return make_refund()


def test_build_refund_basic_0_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        build(None)


def test_build_refund_single_1():
    refund = make_refund(amount=53, count=37)

    result = build(refund)

    assert result.total == 1961


def test_build_refund_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    build(repo, 244)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_refund_edge_3():
    refund = make_refund(amount=87, count=82)

    result = build(refund)

    assert result.total == 7134


def test_build_refund_single_4(refund):
    refund.label = "invoice-626"

    build(refund)

    assert refund.state == "open"
