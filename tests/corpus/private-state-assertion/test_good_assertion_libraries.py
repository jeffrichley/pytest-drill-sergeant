"""Near-misses: assertions made through assertion libraries that read no private
state. Analysed, never run."""

import pytest
from playwright.sync_api import expect
from pytest_check import check

pytestmark = pytest.mark.unit


def test_a_playwright_matcher_on_a_dunder(page):
    page.goto("/scenes")
    expect(page.locator("h1")).to_have_text(page.__class__.__name__)


def test_a_pytest_check_helper_on_a_dunder(cart):
    cart.add("apple")
    check.equal(type(cart).__name__, "Cart")


def test_a_private_read_outside_the_playwright_matcher(page, fake_clock):
    page._clock = fake_clock
    page.goto("/scenes")
    expect(page).to_have_title("Scenes")


def test_a_private_read_outside_the_pytest_check_helper(cart, fake_clock):
    cart._clock = fake_clock
    cart.add("apple")
    check.equal(cart.count, 1)
