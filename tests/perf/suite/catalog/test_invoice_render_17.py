"""Tests for catalog invoice handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_invoice, render


@pytest.fixture
def invoice():
    return make_invoice()


def test_render_invoice_empty_0():
    invoice = make_invoice(amount=84, count=38)

    result = render(invoice)

    assert result.total == 3192


def test_render_invoice_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    render(repo, 81)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_invoice_large_2(invoice):
    invoice.label = "rate-705"

    render(invoice)

    assert invoice.state == "open"


def test_render_invoice_many_3(invoice):
    invoice.label = "invoice-522"

    render(invoice)

    assert invoice.state == "held"


def test_render_invoice_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    render(repo, 333)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_invoice_large_5(invoice):
    invoice.label = "user-529"

    render(invoice)

    assert invoice.state == "done"


def test_render_invoice_many_6_rejects_bad_input():
    with pytest.raises(ValueError, match="invoice"):
        render(None)
