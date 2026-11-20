"""Near-miss: the same three statements appear in each test, but a different line
sits between them each time, so no block of three runs unbroken. Analysed, never
run."""

import pytest
from mail import Inbox, Message, Server

pytestmark = pytest.mark.unit


def test_inbox_receives_a_message():
    server = Server(port=2525)
    inbox = Inbox(server, owner="ann")
    message = Message(to="ann", body="hi")
    server.deliver(message)
    assert inbox.count() == 1


def test_inbox_filters_spam():
    server = Server(port=2525)
    server.enable_spam_filter()
    inbox = Inbox(server, owner="ann")
    spam = Message(to="ann", body="WIN")
    server.deliver(spam)
    assert inbox.count() == 0


def test_inbox_keeps_read_messages():
    server = Server(port=2525)
    server.retain(days=30)
    inbox = Inbox(server, owner="ann")
    server.mark_read_on_delivery()
    server.deliver(Message(to="ann", body="hi"))
    assert inbox.read_count() == 1
