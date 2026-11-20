"""Near-misses: loops that only build data or poll, comprehensions and conditional
expressions, with every assertion outside them. Analysed, never run."""

import pytest


def test_cart_total(cart):
    for sku in ["apple", "pear", "plum"]:
        cart.add(sku, price=2)

    assert cart.total == 6


def test_job_finishes(job, clock):
    job.start()
    while not job.done:
        clock.advance(seconds=1)

    assert job.result == "ok"


def test_active_users(client):
    users = client.get("/users").json()

    assert [u["name"] for u in users if u["active"]] == ["ada", "grace"]


def test_discount_label(pricing):
    label = pricing.label(rate=0.1)

    assert label == ("10% off" if pricing.rounds else "10.0% off")


@pytest.mark.parametrize("text", ["1k", "2m"])
def test_parse_round_trips(parser, text):
    assert parser.format(parser.parse(text)) == text
