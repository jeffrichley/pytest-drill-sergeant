"""Tests for reports rate handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_rate, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_validate_rate_edge_0():
    rate = make_rate(amount=21, count=11)

    result = validate(rate)

    assert result.total == 231


def test_validate_rate_empty_1_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        validate(None)


def test_validate_rate_large_2(rate):
    rate.label = "coupon-841"

    validate(rate)

    assert rate.state == "open"


def test_validate_rate_single_3():
    rate = make_rate(amount=54, count=67)

    result = validate(rate)

    assert result.total == 3618


def test_validate_rate_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        validate(None)
