"""An agent's end-to-end test: every setup step, the act and every check inline, 52
lines from `def` to its last line. Analysed, never run."""


def test_checkout_flow(shop, payments, mailer):  # expect: DS105
    catalog = shop.catalog()
    catalog.add_product(sku="APPLE", name="Apple", price=120, stock=10)
    catalog.add_product(sku="PEAR", name="Pear", price=90, stock=4)
    catalog.add_product(sku="PLUM", name="Plum", price=60, stock=0)
    catalog.add_product(sku="KIWI", name="Kiwi", price=45, stock=25)

    customer = shop.register_customer(
        email="ada@example.com",
        name="Ada Lovelace",
        address={
            "line1": "12 Analytical Row",
            "city": "London",
            "postcode": "N1 9GU",
            "country": "GB",
        },
    )

    cart = shop.new_cart(customer=customer)
    cart.add("APPLE", quantity=3)
    cart.add("PEAR", quantity=2)
    cart.add("KIWI", quantity=6)

    coupon = shop.issue_coupon(code="AUTUMN10", percent_off=10, min_total=500)
    cart.apply_coupon(coupon)

    payments.approve_next(amount=729, reference="pay-001")

    order = shop.checkout(
        cart,
        payment_method="card",
        card={"number": "4242424242424242", "expiry": "12/30", "cvc": "123"},
        delivery="standard",
    )

    assert order.status == "paid"
    assert order.subtotal == 810
    assert order.discount == 81
    assert order.total == 729
    assert order.lines == [
        ("APPLE", 3, 360),
        ("PEAR", 2, 180),
        ("KIWI", 6, 270),
    ]
    assert order.customer_email == "ada@example.com"
    assert order.shipping_address["postcode"] == "N1 9GU"
    assert payments.charges == [("pay-001", 729)]
    assert catalog.stock("APPLE") == 7
    assert catalog.stock("PEAR") == 2
    assert catalog.stock("KIWI") == 19
    assert mailer.sent_to == ["ada@example.com"]
    assert coupon.times_used == 1
