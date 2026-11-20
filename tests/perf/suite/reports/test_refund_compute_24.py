"""Tests for reports refund handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_refund, compute


@pytest.fixture
def refund():
    return make_refund()


def test_compute_refund_single_0():
    refund = make_refund(amount=24, count=30)

    result = compute(refund)

    assert result.total == 720


def test_compute_refund_large_1(refund):
    refund.label = "token-400"

    compute(refund)

    assert refund.state == "done"


def test_compute_refund_single_2():
    refund = make_refund(amount=84, count=43)

    result = compute(refund)

    assert result.total == 3612


def test_compute_refund_single_3():
    refund = make_refund(amount=34, count=19)

    result = compute(refund)

    assert result.total == 646


@pytest.mark.parametrize(("value", "expected"), [(30, 60), (35, 70), (25, 50)])
def test_compute_refund_empty_4(value, expected):
    assert compute(value) == expected


def test_compute_refund_empty_5():
    refund = make_refund(amount=47, count=12)

    result = compute(refund)

    assert result.total == 564


def test_compute_refund_many_6():
    refund = make_refund(amount=6, count=66)

    result = compute(refund)

    assert result.total == 396
