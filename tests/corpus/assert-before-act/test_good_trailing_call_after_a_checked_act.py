"""Near-misses: an act, an assertion on it, then a call after the last assertion.
An act comes before the last assertion, so the trailing call is not DS103's: cleanup
or a second unchecked act is a separate check's (#208). Modelled on stagehand's
`await house.close()` and home-assistant's trailing `reset_mock()`.
Analysed, never run."""

import os
import shutil

import pytest

pytestmark = pytest.mark.unit


def test_register_then_rename(registry):
    registry.register("ada")
    assert registry.names() == ["ada"]
    registry.rename("ada", "grace")


def test_writes_report_then_cleans_up(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    os.remove(path)
    shutil.rmtree(tmp_path / "cache")


def test_server_answers_then_stops(server):
    reply = server.request("/ping")
    assert reply == "pong"
    server.stop()


def test_notifier_reset_after(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()


async def test_house_opens_then_closes(house):
    await house.open()
    assert house.is_open
    await house.close()


def test_guard_act_check_then_trailing_call(cart):
    assert cart.items == []
    cart.add("apple")
    assert cart.items == ["apple"]
    cart.clear()
