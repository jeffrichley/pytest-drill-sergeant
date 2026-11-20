"""Near-misses: mocks that carry the real interface. Analysed, never run."""

from unittest import mock
from unittest.mock import MagicMock, create_autospec

from shop import Mailer, Sender, notify, render


def test_spec_keyword():
    sender = mock.Mock(spec=Sender)
    assert notify(sender, "hi").delivered == 1


def test_spec_positional_and_spec_set():
    page = MagicMock(Mailer)
    template = mock.NonCallableMagicMock(spec_set=Mailer)
    assert render(page, template) == "<p>"


def test_autospec():
    sender = create_autospec(Sender, instance=True)
    assert notify(sender, "hi").delivered == 1


def test_mocker_autospec_and_spy(mocker):
    sender = mocker.create_autospec(Sender, instance=True)
    spy = mocker.spy(Mailer, "deliver")
    assert notify(sender, "hi").delivered == spy.call_count
