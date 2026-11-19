"""Async tests that wait out real time instead of yielding. Analysed, never run."""

import asyncio

import pytest
from poller import Poller

DELAY = 0.2


@pytest.mark.asyncio
async def test_poller_picks_up_the_job():
    poller = Poller()
    poller.submit("job")
    await asyncio.sleep(1)  # expect: DS801
    assert poller.seen == ["job"]


@pytest.mark.asyncio
async def test_poller_waits_a_named_delay():
    poller = Poller()
    poller.submit("job")
    await asyncio.sleep(DELAY)  # expect: DS801
    assert poller.seen == ["job"]
