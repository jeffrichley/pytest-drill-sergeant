"""Tests whose only assertions check how a mock was called, never the outcome.
Analysed, never run."""

from unittest import mock

from shop import Sender, notify, notify_all


def test_notify_sends():  # expect: DS301
    sender = mock.Mock(spec=Sender)
    notify(sender, "hi")
    sender.send.assert_called_once_with("hi")


def test_called_flag(mocker):  # expect: DS301
    send = mocker.patch("shop.send", autospec=True)
    notify_all(["a"])
    assert send.called


def test_call_count_and_args():  # expect: DS301
    with mock.patch("shop.send", autospec=True) as send:
        notify_all(["a", "b"])
    assert send.call_count == 2
    assert send.call_args == mock.call("b")
    assert len(send.call_args_list) == 2


# Moved from no-real-assertion/test_good_assertion_calls.py: a mock verification is
# a real assertion (DS101 stays quiet), but it is the test's only one.
def test_mock_verification_is_an_assertion():  # expect: DS301
    sender = mock.Mock()
    notify(sender, "hi")
    sender.send.assert_called_once_with("hi")
