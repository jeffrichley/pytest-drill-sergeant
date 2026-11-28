"""Near-misses: a `mocker` parameter in a project that declares no pytest-mock, so
nothing the file shows makes its calls the mock library's. Analysed, never run."""

import pytest
from shop import Mailer, Notifier, notify

pytestmark = pytest.mark.unit


def test_notify_with_undeclared_mocker(mocker):
    sender = mocker.Mock()
    assert notify(sender, "hey").delivered == 1


def test_ping_with_undeclared_mocker(mocker):
    mocker.patch.object(Mailer, "deliver", return_value=False)
    assert Notifier(mocker.MagicMock()).ping() == "queued"
