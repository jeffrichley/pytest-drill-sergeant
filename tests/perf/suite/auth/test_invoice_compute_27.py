"""Tests for auth invoice handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_invoice, compute


@pytest.fixture
def invoice():
    return make_invoice()


def test_compute_invoice_large_0(invoice):
    invoice.label = "report-878"

    compute(invoice)

    assert invoice.state == "done"


def test_compute_invoice_many_1(invoice):
    invoice.label = "user-926"

    compute(invoice)

    assert invoice.state == "open"


def test_compute_invoice_many_2():
    invoice = make_invoice(amount=64, count=48)

    result = compute(invoice)

    assert result.total == 3072


def test_compute_invoice_large_3_works():
    result = compute(make_invoice())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (28, 56), (38, 76)])
def test_compute_invoice_empty_4(value, expected):
    assert compute(value) == expected


def test_compute_invoice_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    compute(repo, 282)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_invoice_large_6():
    invoice = make_invoice(amount=35, count=44)

    result = compute(invoice)

    assert result.total == 1540


def test_compute_invoice_single_7(invoice):
    invoice.label = "item-710"

    compute(invoice)

    assert invoice.state == "open"


def test_compute_invoice_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    compute(repo, 260)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
