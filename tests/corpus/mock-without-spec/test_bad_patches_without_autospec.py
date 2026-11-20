"""Patches that put a spec-less mock in place: as a `with`, a decorator, and on a
class. Analysed, never run."""

from unittest import mock
from unittest.mock import patch

import pytest
from shop import Mailer, Notifier, label, notify_all

pytestmark = pytest.mark.unit


def test_label_with_a_patched_clock():
    with mock.patch("shop.today", return_value="2026-01-01"):  # expect: DS302
        assert label() == "Today: 2026-01-01"


@patch("shop.send")  # expect: DS302
def test_notify_all_counts(send):
    assert notify_all(["a", "b"]) == 2


class TestNotifier:
    @patch.object(Mailer, "deliver")  # expect: DS302
    def test_ping_reports(self, deliver):
        assert Notifier().ping() == "sent"
