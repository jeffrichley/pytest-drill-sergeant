"""Tests for inventory invoice handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_invoice, parse


@pytest.fixture
def invoice():
    return make_invoice()


def test_parse_invoice_many_0():
    invoice = make_invoice(amount=69, count=29)

    result = parse(invoice)

    assert result.total == 2001


def test_parse_invoice_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    parse(repo, 184)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_invoice_basic_2():
    invoice = make_invoice(amount=46, count=6)

    result = parse(invoice)

    assert result.total == 276


def test_parse_invoice_many_3():
    invoice = make_invoice(amount=40, count=11)

    result = parse(invoice)

    assert result.total == 440


def test_parse_invoice_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    parse(repo, 259)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (43, 86), (32, 64)])
def test_parse_invoice_large_5(value, expected):
    assert parse(value) == expected


def test_parse_invoice_single_6():
    invoice = make_invoice(amount=34, count=60)

    result = parse(invoice)

    assert result.total == 2040


def test_parse_invoice_single_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    parse(repo, 283)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_invoice_large_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_invoice()

    parse(repo, 358)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
