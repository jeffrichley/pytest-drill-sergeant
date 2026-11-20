"""A call between checks that only its name suggests is a reset or cleanup: nothing
the file says makes it so, so it is a second act. Analysed, never run."""


def test_mock_reset_between_checks(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()  # expect: DS104
    assert sender.send.call_count == 0


def test_closed_between_checks(conn):
    conn.send("ping")
    assert conn.sent == ["ping"]
    conn.close()  # expect: DS104
    assert conn.closed
