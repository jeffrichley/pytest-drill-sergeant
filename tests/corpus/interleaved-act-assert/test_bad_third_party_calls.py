"""Tests whose acts go into a third-party package, code the check can't see. DS103
lets such a call pass as one that may assert; for DS104 it stays an act, as a
Playwright click or fill does, so each test still has three act-then-assert cycles.
Analysed, never run."""

import pytest
from playwright.async_api import expect
from pytest_homeassistant.common import async_fire_time_changed

pytestmark = pytest.mark.unit


async def test_clicks_between_checks(page):
    await page.get_by_role("button", name="Add").click()
    await expect(page.get_by_test_id("count")).to_have_text("1")
    await page.get_by_role("button", name="Add").click()  # expect: DS104
    await expect(page.get_by_test_id("count")).to_have_text("2")
    await page.get_by_role("button", name="Reset").click()
    await expect(page.get_by_test_id("count")).to_have_text("0")


async def test_time_fired_between_checks(hass, light):
    await light.turn_on()
    assert light.is_on
    async_fire_time_changed(hass)  # expect: DS104
    assert light.brightness == 255
    async_fire_time_changed(hass)
    assert not light.is_on
