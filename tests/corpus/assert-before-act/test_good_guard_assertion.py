"""Near-misses: a guard assertion before the act, with the outcome asserted after it.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_add_item(cart):
    assert cart.items == []
    cart.add("apple")
    assert cart.items == ["apple"]


async def test_send_message(client):
    assert client.connected
    await client.send("hello")
    client.outbox.assert_called_once_with("hello")


def test_load_rows(importer, rows):
    assert importer.count() == 0
    for row in rows:
        importer.load(row)
    assert importer.count() == len(rows)
