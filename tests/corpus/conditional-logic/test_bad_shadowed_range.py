"""A loop that looks like a deliberate repeat, but `range` is the file's import, not
Python's builtin, so how many times it runs is not known. Analysed, never run."""

import pytest
from pagination import range  # noqa: A004 -- the shadowing is the near-miss

pytestmark = pytest.mark.unit


def test_reconnecting_twice(client):
    for _ in range(2):  # expect: DS107
        client.reconnect()
        assert client.connected
