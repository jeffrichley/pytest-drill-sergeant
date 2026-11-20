"""Near-duplicates inside one test class, decorated alike, among tests that differ.
Analysed, never run."""

import pytest
from shop import Cart

pytestmark = pytest.mark.unit


class TestDiscounts:
    @pytest.mark.slow
    def test_ten_percent_off(self, cart):  # expect: DS502
        cart.discount(10)
        assert cart.total() == 90

    @pytest.mark.slow
    def test_half_off(self, cart):
        cart.discount(50)
        assert cart.total() == 50

    def test_discount_is_listed(self, cart):
        cart.discount(10)
        assert cart.lines[-1].label == "10% off"

    @pytest.mark.slow
    def test_no_discount(self, cart):
        cart.discount(0)
        assert cart.total() == 100


def test_cart_starts_full_price():
    assert Cart().total() == 100
