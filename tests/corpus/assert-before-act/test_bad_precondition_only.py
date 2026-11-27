"""Tests that assert only the starting state they are handed, then act, and never
check what the act did: nothing runs before the last assertion. A name never makes
a call anything but an act. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_add_item(cart):
    assert cart.items == []
    cart.add("apple")  # expect: DS103


def test_add_two_items(cart):
    assert cart.items == []
    assert not cart.total
    cart.add("apple")  # expect: DS103
    cart.add("pear")


async def test_send_message(client):
    assert client.connected
    await client.send("hello")  # expect: DS103


def test_import_rows(importer, rows):
    assert importer.loaded == 0
    for row in rows:  # expect: DS103
        importer.load(row)


def test_stop_named_like_cleanup(server):
    assert server.running
    server.stop()  # expect: DS103


def test_add_after_guards_that_only_look(cart):
    assert len(cart.items) == 0
    assert isinstance(cart.items, list)
    cart.add("apple")  # expect: DS103
