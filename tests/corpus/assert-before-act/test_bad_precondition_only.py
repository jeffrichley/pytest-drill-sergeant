"""Tests that assert the starting state, then act, and never check what the act did.
Analysed, never run."""


class Cart:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)


def test_add_item():
    cart = Cart()
    assert cart.items == []
    cart.add("apple")  # expect: DS103


def test_add_two_items():
    cart = Cart()
    assert len(cart.items) == 0
    assert not cart.items
    cart.add("apple")  # expect: DS103
    cart.add("pear")


async def test_send_message(client):
    assert client.connected
    await client.send("hello")  # expect: DS103
