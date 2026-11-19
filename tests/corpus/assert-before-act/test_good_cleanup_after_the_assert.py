"""Near-misses: what runs after the last assertion is cleanup or output, not an act.
Analysed, never run."""

import logging
import os
import shutil

import pytest

log = logging.getLogger(__name__)


def test_server_answers(server):
    reply = server.request("/ping")
    assert reply == "pong"
    server.stop()


def test_writes_report(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    path.unlink()


def test_notifier_sends(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()
    print("sent")


def test_files_removed_and_logged_after(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    os.remove(path)
    os.unlink(tmp_path / "lock")
    shutil.rmtree(tmp_path / "cache")
    logging.getLogger("tests").debug("checked")
    log.info("done")


def test_match_after_the_raises(parser):
    with pytest.raises(ValueError) as excinfo:
        parser.parse("x")
    assert excinfo.type is ValueError
    excinfo.match("invalid")
