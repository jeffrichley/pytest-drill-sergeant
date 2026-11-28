"""pytest-mock's fixture making spec-less mocks. Analysed, never run."""

import pytest
from shop import Mailer, Notifier, label, notify

pytestmark = pytest.mark.unit


def test_notify_with_mocker(mocker):
    sender = mocker.Mock()  # expect: DS302
    assert notify(sender, "hi").delivered == 1


def test_label_with_mocker(mocker):
    mocker.patch("shop.today", return_value="2026-01-01")  # expect: DS302
    assert label() == "Today: 2026-01-01"


def test_ping_with_mocker(mocker):
    mocker.patch.object(Mailer, "deliver", return_value=True)  # expect: DS302
    page = mocker.MagicMock()  # expect: DS302
    assert Notifier(page).ping() == "sent"
