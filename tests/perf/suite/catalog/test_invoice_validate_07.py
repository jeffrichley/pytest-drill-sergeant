"""Tests for catalog invoice handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_invoice, validate


@pytest.fixture
def invoice():
    return make_invoice()


def test_validate_invoice_large_0(invoice):
    invoice.label = "event-195"

    validate(invoice)

    assert invoice.state == "open"


def test_validate_invoice_single_1(invoice):
    invoice.label = "report-292"

    validate(invoice)

    assert invoice.state == "held"


def test_validate_invoice_single_2():
    invoice = make_invoice(amount=62, count=56)

    result = validate(invoice)

    assert result.total == 3472


def test_validate_invoice_basic_3():
    invoice = make_invoice(amount=41, count=46)

    result = validate(invoice)

    assert result.total == 1886
