"""An agent's end-to-end test: every setup step, the act and every check inline, 55
lines of code from `def` to its last line, with no blank line, comment, docstring or
data table to discount. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_checkout_flow(shop, payments, mailer):  # expect: DS105
    catalog = shop.catalog()
    catalog.add_product(sku="APPLE", name="Apple", price=120, stock=10)
    catalog.add_product(sku="PEAR", name="Pear", price=90, stock=4)
    catalog.add_product(sku="PLUM", name="Plum", price=60, stock=0)
    catalog.add_product(sku="KIWI", name="Kiwi", price=45, stock=25)
    catalog.add_product(sku="FIG", name="Fig", price=150, stock=8)
    catalog.add_product(sku="DATE", name="Date", price=70, stock=12)
    customer = shop.register_customer(
        email="ada@example.com",
        name="Ada Lovelace",
        address=shop.address(line1="12 Analytical Row", postcode="N1 9GU"),
    )
    cart = shop.new_cart(customer=customer)
    cart.add("APPLE", quantity=3)
    cart.add("PEAR", quantity=2)
    cart.add("KIWI", quantity=6)
    cart.add("FIG", quantity=1)
    cart.remove("FIG")
    cart.add("DATE", quantity=2)
    cart.remove("DATE")
    coupon = shop.issue_coupon(code="AUTUMN10", percent_off=10, min_total=500)
    cart.apply_coupon(coupon)
    payments.approve_next(amount=729, reference="pay-001")
    order = shop.checkout(
        cart,
        payment_method="card",
        card=payments.test_card(),
        delivery="standard",
    )
    assert order.status == "paid"
    assert order.subtotal == 810
    assert order.discount == 81
    assert order.total == 729
    assert order.lines[0] == ("APPLE", 3, 360)
    assert order.lines[1] == ("PEAR", 2, 180)
    assert order.lines[2] == ("KIWI", 6, 270)
    assert len(order.lines) == 3
    assert order.customer_email == "ada@example.com"
    assert order.shipping_address.postcode == "N1 9GU"
    assert payments.charges == [("pay-001", 729)]
    assert catalog.stock("APPLE") == 7
    assert catalog.stock("PEAR") == 2
    assert catalog.stock("KIWI") == 19
    assert catalog.stock("FIG") == 8
    assert catalog.stock("DATE") == 12
    assert catalog.stock("PLUM") == 0
    assert mailer.sent_to == ["ada@example.com"]
    assert mailer.subjects == ["Your order is on its way"]
    assert coupon.times_used == 1
    assert coupon.remaining_uses == 0
    assert customer.order_count == 1
    assert customer.lifetime_spend == 729
    assert shop.open_carts() == []
    assert shop.orders() == [order]
