"""Near-misses: assertions made through assertion libraries, known by the file's
imports. Analysed, never run."""

import pytest
import pytest_check
from assertpy import assert_that
from playwright.async_api import expect
from playwright.sync_api import expect as sync_expect
from pytest_check import check
from pytest_check import equal as check_equal

pytestmark = pytest.mark.unit


async def test_a_role_chosen_while_the_scene_is_still_loading_is_not_lost(room):
    director = room.get_by_role("button", name="Director")
    await room.click("text=Join")
    await expect(director).to_be_disabled()


async def test_a_negated_playwright_matcher_is_an_assertion(page):
    await page.goto("/scenes")
    await expect(page.locator("h1")).not_to_have_text("Loading")


def test_a_sync_playwright_matcher_is_an_assertion(page):
    page.goto("/scenes")
    sync_expect(page).to_have_title("Scenes")


def test_a_pytest_check_helper_is_an_assertion(cart):
    cart.add("apple")
    check.equal(cart.count, 1)


def test_a_pytest_check_module_helper_is_an_assertion(cart):
    cart.add("apple")
    pytest_check.is_in("apple", cart.items)


def test_a_pytest_check_helper_imported_by_name_is_an_assertion(cart):
    cart.add("apple")
    check_equal(cart.count, 1)


def test_an_assertpy_chain_is_an_assertion(cart):
    cart.add("apple")
    assert_that(cart.items).contains("apple")


def test_a_pytest_check_function_from_its_module_is_an_assertion(cart):
    from pytest_check.check_functions import is_true

    cart.add("apple")
    is_true(cart.count == 1)
