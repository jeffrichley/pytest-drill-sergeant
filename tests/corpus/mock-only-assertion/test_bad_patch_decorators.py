"""Mocks handed in by `patch` decorators, in plain and class-based tests. Analysed,
never run."""

from unittest import mock
from unittest.mock import patch

from shop import Mailer, Notifier, notify_all


@mock.patch("shop.audit", autospec=True)
@mock.patch("shop.send", autospec=True)
def test_both_called(send, audit):  # expect: DS301
    notify_all(["a"])
    send.assert_called_once_with("a")
    audit.assert_called_once()


class TestNotifier:
    @patch.object(Mailer, "deliver", autospec=True)
    def test_delivers(self, deliver):  # expect: DS301
        Notifier().ping()
        deliver.assert_called()

    @patch("shop.log", autospec=True)
    def test_logs_through_an_alias(self, log):  # expect: DS301
        write = log.write
        Notifier().ping()
        write.assert_called_once_with("ping")
