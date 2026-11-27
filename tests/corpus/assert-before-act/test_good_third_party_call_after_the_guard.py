"""Near-misses: the call after the last assertion goes into a third-party package,
code the check can't see, so it may assert and isn't an act. Modelled on
home-assistant's `help_test_*` helpers from `pytest_homeassistant`.
Analysed, never run."""

import pytest
from pytest_homeassistant.common import async_fire_time_changed
from pytest_homeassistant.components.mqtt.common import help_test_unique_id

pytestmark = pytest.mark.unit


async def test_guard_then_a_third_party_helper(hass):
    assert hass.state == "running"
    await help_test_unique_id(hass, "light")


async def test_act_checked_then_a_third_party_call(hass, light):
    await light.turn_on()
    assert light.is_on
    async_fire_time_changed(hass)
