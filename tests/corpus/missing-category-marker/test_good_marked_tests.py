"""Category markers on the test, through whatever name the imports give pytest.

Analysed, never run.
"""

import pytest
import pytest as pt
from pytest import mark
from pytest import mark as m
from thermostat import Thermostat


@pytest.mark.unit
def test_thermostat_starts_at_twenty():
    assert Thermostat().target() == 20


@pytest.mark.slow
@pytest.mark.integration()
def test_thermostat_heats_the_room():
    thermostat = Thermostat()
    thermostat.set(25)
    assert thermostat.heater_on()


@pt.mark.e2e
def test_thermostat_shows_the_target_on_its_screen():
    thermostat = Thermostat()
    thermostat.set(18)
    assert thermostat.screen() == "18"


@mark.unit
def test_thermostat_rejects_a_target_below_freezing():
    with pytest.raises(ValueError, match="below 0"):
        Thermostat().set(-5)


@m.unit
@pytest.mark.parametrize("target", [10, 30])
async def test_thermostat_accepts_a_target_in_range(target):
    thermostat = Thermostat()
    await thermostat.set_async(target)
    assert thermostat.target() == target
