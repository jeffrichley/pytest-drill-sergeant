"""Near-misses: code runs before the last assertion, so the assertions check an act:
a value made by a call (assigned, or bound by a `with`), an `await` kept, a call
inside an assertion, pytest's call form, a `with` on code outside the standard
library, a bare call into a third-party package. A call after them is a trailing
call, a separate check's (#208), not DS103's. Modelled on stagehand's `reply =
await client.post(...)` then `await house.close()`, networkx's `pytest.raises(E,
nx.watts_strogatz_graph, ...)` and pandas' `with ExcelWriter(...) as writer:`.
Analysed, never run."""

import httpx
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


def test_call_form_raises_then_called_again(graph_maker):
    pytest.raises(ValueError, graph_maker.make, 10, 11)
    graph_maker.make(10, 9)


def test_writer_made_by_the_with_then_written(tmp_path, writer_class):
    with writer_class(tmp_path, engine="fast") as writer:
        assert writer.book.write_only is False
        writer.write([])


def test_one_line_with_then_unlinked(path):
    with open(path) as f: assert f.readable  # noqa: E701  # fmt: skip
    path.unlink()


def test_app_run_by_a_with_then_shut_down(app):
    with app.running():
        assert app.up
    app.shutdown()


def test_third_party_act_checked_then_reset(server):
    httpx.post(server.url, json={})
    assert server.received == 1
    server.reset()
