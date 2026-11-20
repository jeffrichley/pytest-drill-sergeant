"""Tests for inventory invoice handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_invoice, compute


@pytest.fixture
def invoice():
    return make_invoice()


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (3, 6), (20, 40)])
def test_compute_invoice_many_0(value, expected):
    assert compute(value) == expected


def test_compute_invoice_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        compute(None)


def test_compute_invoice_empty_2():
    invoice = make_invoice(amount=6, count=40)

    result = compute(invoice)

    assert result.total == 240


def test_compute_invoice_basic_3_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        compute(None)


def test_compute_invoice_edge_4(invoice):
    invoice.label = "cart-414"

    compute(invoice)

    assert invoice.state == "open"


def test_compute_invoice_single_5():
    invoice = make_invoice(amount=47, count=71)

    result = compute(invoice)

    assert result.total == 3337


def test_compute_invoice_basic_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    compute(repo, 334)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_invoice_large_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    compute(repo, 306)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
