"""Assertions on private state made through assertion libraries, known by the file's
imports. Analysed, never run."""

import pytest
import pytest_check
from playwright.async_api import expect
from playwright.sync_api import expect as sync_expect
from pytest_check import check
from pytest_check import equal as check_equal

pytestmark = pytest.mark.unit


async def test_a_playwright_matcher_on_a_private_locator(page):
    await page.goto("/scenes")
    await expect(page._banner).to_have_text("Scenes")  # expect: DS602


def test_a_sync_playwright_matcher_with_a_private_argument(page, scene):
    page.goto("/scenes")
    sync_expect(page).to_have_title(scene._title)  # expect: DS602


def test_a_pytest_check_helper_on_private_state(cart):
    cart.add("apple")
    check.equal(cart._total, 3)  # expect: DS602


def test_a_pytest_check_module_helper_on_private_state(cart):
    cart.add("apple")
    pytest_check.is_in("apple", cart._items)  # expect: DS602


def test_a_pytest_check_helper_imported_by_name_on_private_state(cart):
    cart.add("apple")
    check_equal(cart._count, 1)  # expect: DS602
