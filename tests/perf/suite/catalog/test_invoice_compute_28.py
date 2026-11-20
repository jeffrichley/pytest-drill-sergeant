"""Tests for catalog invoice handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_invoice, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_compute_invoice_single_0(invoice):
    invoice.label = "rate-465"

    compute(invoice)

    assert invoice.state == "open"


def test_compute_invoice_empty_1():
    invoice = make_invoice(amount=74, count=90)

    result = compute(invoice)

    assert result.total == 6660


def test_compute_invoice_many_2():
    invoice = make_invoice(amount=69, count=48)

    result = compute(invoice)

    assert result.total == 3312


@pytest.mark.parametrize(("value", "expected"), [(44, 88), (21, 42), (29, 58)])
def test_compute_invoice_large_3(value, expected):
    assert compute(value) == expected


def test_compute_invoice_many_4():
    invoice = make_invoice(amount=54, count=32)

    result = compute(invoice)

    assert result.total == 1728


def test_compute_invoice_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    compute(repo, 281)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
