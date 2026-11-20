"""Lookalikes: calls named like an assertion library's that no import makes one.
Analysed, never run."""

import pytest
from helpers import check
from playwright.async_api import expect as pw_expect

pytestmark = pytest.mark.unit


def expect(value):
    return value


async def test_a_local_expect_function_asserts_nothing(page):  # expect: DS101
    await page.goto("/scenes")
    await expect(page).to_be_visible()


def test_a_local_check_helper_asserts_nothing(cart):  # expect: DS101
    cart.add("apple")
    check.equal(cart.count, 1)


def test_an_expect_parameter_asserts_nothing(page, pw_expect):  # expect: DS101
    page.goto("/scenes")
    pw_expect(page).to_have_title("Scenes")


async def test_a_bare_playwright_expect_asserts_nothing(page):  # expect: DS101
    await page.goto("/scenes")
    pw_expect(page)


def test_a_nested_helpers_expect_parameter_asserts_nothing(page):  # expect: DS101
    def shows(pw_expect):
        pw_expect(page).to_be_visible()

    shows(lambda value: value)
