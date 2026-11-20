"""Tests whose structure leaves no place for one AAA comment or another: an act
after the last assertion, an assertion under `# Act` beside a `# Assert`, a `# Assert` with nothing
asserted under it, and a
test with no assertion, which is DS101's alone. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_close_after_checking(conn):  # expect: DS108
    conn.open()
    assert conn.is_open
    conn.close()


def test_send_twice(outbox):
    # Act - # expect: DS108
    outbox.send("hi")
    assert outbox.count() == 1
    # Assert
    assert outbox.last() == "hi"


def test_refund_then_cancel(order):
    # Arrange
    assert order.total == 10
    # Act - # expect: DS108
    expected = 0
    # Assert - # expect: DS108
    print(expected)
    order.cancel()  # expect: DS103


def test_tally(counter):
    # Arrange
    assert counter.value == 0
    # Act
    total = counter.bump()
    # Assert - # expect: DS108
    print(total)


def test_archive(store):  # expect: DS101
    # Act
    store.archive()
