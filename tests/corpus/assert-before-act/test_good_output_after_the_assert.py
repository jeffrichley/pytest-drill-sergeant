"""Near-misses: what runs after the last assertion is known to be output or one of
pytest's own fixtures, never an act. Known from the imports, a module-level logger
or a fixture taken as a parameter. Analysed, never run."""

import logging

import pytest

pytestmark = pytest.mark.unit

log = logging.getLogger(__name__)


def test_notifier_sends(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    print("sent")


def test_logged_after(report):
    report.write()
    assert report.done
    logging.info("written")
    logging.getLogger("tests").debug("checked")
    log.info("done")


def test_fixtures_used_after(caplog, capsys, recwarn, monkeypatch, greeter):
    greeter.greet("Ada")
    assert greeter.greeted == ["Ada"]
    caplog.clear()
    capsys.readouterr()
    recwarn.clear()
    monkeypatch.undo()


def test_match_after_the_raises(parser):
    with pytest.raises(ValueError) as excinfo:
        parser.parse("x")
    assert excinfo.type is ValueError
    excinfo.match("invalid")
