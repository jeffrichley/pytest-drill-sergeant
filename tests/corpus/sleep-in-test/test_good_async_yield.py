"""Near-misses: `asyncio.sleep(0)` yields to the event loop without waiting.

Analysed, never run.
"""

import asyncio

import pytest
from poller import Poller

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_poller_runs_after_one_tick():
    poller = Poller()
    poller.submit("job")
    await asyncio.sleep(0)
    assert poller.seen == ["job"]


@pytest.mark.asyncio
async def test_poller_runs_after_a_float_zero_tick():
    poller = Poller()
    poller.submit("job")
    await asyncio.sleep(0.0)
    assert poller.done == ["job"]
