"""Tests for orders refund handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_refund, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def refund():
    return make_refund()


def test_compute_refund_single_0_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        compute(None)


def test_compute_refund_edge_1():
    refund = make_refund(amount=92, count=73)

    result = compute(refund)

    assert result.total == 6716


def test_compute_refund_large_2():
    refund = make_refund(amount=9, count=90)

    result = compute(refund)

    assert result.total == 810


def test_compute_refund_large_3_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        compute(None)


def test_compute_refund_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        compute(None)


def test_compute_refund_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    compute(repo, 479)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
