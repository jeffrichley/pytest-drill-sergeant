"""Expected values taken from the code under test through a name.
Analysed, never run."""

from shop import gross_price, slugify


def test_gross_price():
    expected = gross_price(100, 20)
    assert gross_price(100, 20) == expected  # expect: DS203


def test_slug_result_matches():
    result = slugify("Hello World")
    expected = slugify("Hello World")
    assert result == expected  # expect: DS203


async def test_async_gross_price(client):
    actual = await client.gross_price(100, 20)
    assert actual == await client.gross_price(100, 20)  # expect: DS203
