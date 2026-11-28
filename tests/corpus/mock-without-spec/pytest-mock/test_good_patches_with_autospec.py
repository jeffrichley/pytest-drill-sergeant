"""Near-misses: patches with `autospec`, patches told what to put in place, and
patches that make no mock. Analysed, never run."""

import os
from unittest import mock
from unittest.mock import PropertyMock, patch

import pytest
from shop import Clock, FakeClock, Mailer, Notifier, greeting, label, notify_all

pytestmark = pytest.mark.unit


@patch("shop.send", autospec=True)
def test_notify_all_counts(send):
    assert notify_all(["a", "b"]) == 2


def test_patch_object_autospec(mocker):
    mocker.patch.object(Mailer, "deliver", autospec=True, return_value=True)
    assert Notifier().ping() == "sent"


def test_new_in_place():
    with mock.patch("shop.today", new=lambda: "2026-01-01"):
        assert label() == "Today: 2026-01-01"


def test_new_positional():
    with patch.object(Clock, "now", FakeClock()), patch("shop.tz", "UTC"):
        assert label() == "Today: 2026-01-01"


def test_property_and_dict():
    with (
        patch.object(Mailer, "host", new_callable=PropertyMock) as host,
        patch.dict(os.environ, {"LANG": "fr"}),
    ):
        host.return_value = "mx"
        assert greeting() == "bonjour mx"
