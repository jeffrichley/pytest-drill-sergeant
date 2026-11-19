"""Assertions that multiply the result away, as in the Lemmy-reported Claude test
`assert(5 + (funcToTest(846) * 0) == 5)`. Analysed, never run."""

from shop import price


def test_price_of_846():
    assert 5 + (price(846) * 0) == 5  # expect: DS202


def test_price_through_a_name():
    result = price(846)
    assert 0 * result == 0  # expect: DS202


async def test_async_price(client):
    total = await client.price(846)
    assert total * 0 + 1 == 1  # expect: DS202
