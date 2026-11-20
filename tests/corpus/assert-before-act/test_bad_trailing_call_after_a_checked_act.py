"""An act, an assertion on it, then a call after the last assertion: an act nothing
checks, or cleanup that never runs when an assertion fails. Whatever came before,
an assigned call, an `await` inside the assertion, a `with` or pytest's call form,
the trailing call is flagged. Modelled on stagehand's `reply = await
client.post(...)` then `await house.close()`, and home-assistant's trailing
`reset_mock()`. Analysed, never run."""

import os
import shutil

import pytest

pytestmark = pytest.mark.unit


class Cart:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)


def test_add_item():
    cart = Cart()
    assert cart.items == []
    cart.add("apple")  # expect: DS103


async def test_reply_checked_then_closed(client, house):
    reply = await client.post("/launch/begin")
    assert reply.json()["ok"]
    await house.close()  # expect: DS103


async def test_act_inside_the_assertion_then_closed(run):
    assert (await run.submit("spawn")).ok
    await run.submit("close")  # expect: DS103


def test_register_then_rename(registry):
    registry.register("ada")
    assert registry.names() == ["ada"]
    registry.rename("ada", "grace")  # expect: DS103


def test_writes_report_then_cleans_up(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    os.remove(path)  # expect: DS103
    shutil.rmtree(tmp_path / "cache")


def test_notifier_reset_after(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()  # expect: DS103


def test_call_form_raises_then_called_again(graph_maker):
    pytest.raises(ValueError, graph_maker.make, 10, 11)
    graph_maker.make(10, 9)  # expect: DS103


def test_writer_made_by_the_with_then_written(tmp_path, writer_class):
    with writer_class(tmp_path, engine="fast") as writer:
        assert writer.book.write_only is False
        writer.write([])  # expect: DS103


class TestJob:
    def test_job_logs(self, job):
        job.run()
        assert job.done
        self.log.info("ran")  # expect: DS103
