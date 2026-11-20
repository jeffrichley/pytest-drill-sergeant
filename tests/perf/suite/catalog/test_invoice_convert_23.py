"""Tests for catalog invoice handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_invoice, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def invoice():
    return make_invoice()


def test_convert_invoice_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    convert(repo, 198)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_invoice_basic_1(invoice):
    invoice.label = "invoice-47"

    convert(invoice)

    assert invoice.state == "open"


@pytest.mark.parametrize(("value", "expected"), [(28, 56), (13, 26), (38, 76)])
def test_convert_invoice_large_2(value, expected):
    assert convert(value) == expected


def test_convert_invoice_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    convert(repo, 408)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (9, 18), (47, 94)])
def test_convert_invoice_basic_4(value, expected):
    assert convert(value) == expected
