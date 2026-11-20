"""The golden suite's checkout tests. Analysed by the golden test, never run."""

import pytest

from shop.checkout import Checkout

pytestmark = pytest.mark.integration


def test_checkout_applies_and_removes_a_discount_code(basket):
    checkout = Checkout(basket)

    checkout.apply_code("SPRING10")
    assert checkout.discount == 10
    checkout.remove_code()
    assert checkout.discount == 0


def test_checkout_places_the_order(basket, payments):
    checkout = Checkout(basket, payments=payments)

    order = checkout.place()

    assert order.number == "A-1001"
    payments.charge.assert_called_once_with(order.total)
