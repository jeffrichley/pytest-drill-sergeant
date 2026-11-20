"""Near-misses: code runs before the last assertion, so the assertions check an act:
a value made by a call, an `await` kept, a call inside an assertion. A call after
them is a trailing call, a separate check's (#208), not DS103's. Modelled on
stagehand's `reply = await client.post(...)` then `await house.close()`.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


class Cart:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)


def test_made_then_checked_then_added():
    cart = Cart()
    assert cart.items == []
    cart.add("apple")


async def test_reply_checked_then_closed(client, house):
    reply = await client.post("/launch/begin")
    assert reply.json()["ok"]
    await house.close()


async def test_act_inside_the_assertion_then_closed(run):
    assert (await run.submit("spawn")).ok
    await run.submit("close")


def test_count_checked_then_loaded(importer, rows):
    assert importer.count() == 0
    for row in rows:
        importer.load(row)
