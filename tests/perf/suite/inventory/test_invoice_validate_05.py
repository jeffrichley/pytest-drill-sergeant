"""Tests for inventory invoice handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_invoice, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_validate_invoice_large_0_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        validate(None)


@pytest.mark.parametrize(("value", "expected"), [(5, 10), (46, 92), (9, 18)])
def test_validate_invoice_empty_1(value, expected):
    assert validate(value) == expected


def test_validate_invoice_large_2():
    invoice = make_invoice(amount=5, count=41)

    result = validate(invoice)

    assert result.total == 205


def test_validate_invoice_empty_3_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        validate(None)


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (43, 86), (20, 40)])
def test_validate_invoice_many_4(value, expected):
    assert validate(value) == expected
