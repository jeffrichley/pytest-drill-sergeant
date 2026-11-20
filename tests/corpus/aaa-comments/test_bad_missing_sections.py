"""Tests with some AAA comments but not all they need. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_rename_user(users):  # expect: DS108
    # Arrange
    users.create("ada")
    # Act
    users.rename("ada", "grace")
    assert users.names() == ["grace"]


def test_deposit(account):  # expect: DS108
    amount = 50
    # Act
    account.deposit(amount)
    # Assert
    assert account.balance == amount


def test_parse_header(parser):  # expect: DS108
    raw = b"GET / HTTP/1.1"
    # Assert
    assert parser.parse(raw).method == "GET"


async def test_fetch_page(client):  # expect: DS108
    # Act
    page = await client.fetch("/home")
    assert page.status == 200
