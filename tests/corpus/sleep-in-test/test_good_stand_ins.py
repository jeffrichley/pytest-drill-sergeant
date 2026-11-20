"""Near-misses: sleeps inside stand-ins the test hands over and never calls itself.

Modelled on home-assistant `mqtt/test_util.py:88`, `tado/test_init.py:65` and stagehand
`test_human_input.py:166`, `test_run.py:582`. Analysed, never run.
"""

import asyncio
import time
from unittest.mock import patch

import pytest
from engine import Engine, Seat
from jobs import EnsureJobAfterCooldown

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_a_slow_job_handed_over_by_reference_is_cancelled():
    async def slow_job():
        await asyncio.sleep(1.0)

    timer = EnsureJobAfterCooldown(0.0, slow_job)
    timer.cancel()
    assert timer.cancelled


@pytest.mark.asyncio
async def test_a_slow_typist_is_faulted():
    async def slow_typist(view):
        await asyncio.sleep(0.3)
        return "Sit down."

    engine = Engine({"boss": Seat(answer=slow_typist)})
    await engine.play()
    assert engine.faulted == ["boss"]


@pytest.mark.asyncio
async def test_a_stubborn_seat_cannot_hold_close_open():
    class Stubborn(Seat):
        async def play(self, view):
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                await asyncio.sleep(1)
                raise

    engine = Engine({"dee": Stubborn()})
    await engine.close()
    assert engine.closed


def test_a_stand_in_handed_over_as_an_attribute():
    def slow_read():
        time.sleep(2)
        return b""

    engine = Engine({})
    engine.read = slow_read
    assert engine.ready()


def test_a_side_effect_lambda_stalls_the_patched_call():
    with patch("engine.fetch", autospec=True, side_effect=lambda *a: time.sleep(5)):
        engine = Engine({})
        engine.refresh()
    assert engine.stale


@pytest.mark.asyncio
async def test_a_stand_in_rebound_before_the_call_is_not_the_one_called():
    async def slow_job():
        await asyncio.sleep(1.0)

    timer = EnsureJobAfterCooldown(0.0, slow_job)
    slow_job = timer.run
    await slow_job()
    assert timer.ran


def test_a_parameter_hides_the_stand_in_of_the_same_name():
    def settle():
        time.sleep(0.5)

    def run(settle):
        settle()

    engine = Engine({"settle": settle})
    run(engine.join)
    assert engine.closed
