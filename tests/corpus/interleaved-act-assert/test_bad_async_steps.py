"""Awaited acts interleaved with assertions. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


async def test_connection(conn):
    await conn.open()
    assert conn.is_open
    await conn.send("ping")  # expect: DS104
    conn.on_send.assert_called_once()


class TestDoor:
    async def test_door(self, door):
        await door.unlock()
        assert not door.locked
        await door.lock()  # expect: DS104
        assert door.locked
