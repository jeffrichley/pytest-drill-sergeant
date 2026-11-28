"""`pytest.raises` blocks whose only statement raises the expected exception itself,
as networkx `tests/test_exceptions.py:13`-`:38` do (`with
pytest.raises(nx.NetworkXError): raise nx.NetworkXError`): nothing but the test
can raise it. Analysed, never run."""

import pytest
import shop
from pytest import raises
from shop import OutOfStock

pytestmark = pytest.mark.unit


def test_raises_out_of_stock():
    with pytest.raises(OutOfStock):  # expect: DS202
        raise OutOfStock


def test_raises_through_the_module():
    with pytest.raises(shop.OutOfStock):  # expect: DS202
        raise shop.OutOfStock("sold out")


def test_raises_by_keyword_with_match():
    with pytest.raises(expected_exception=OutOfStock, match="sold"):  # expect: DS202
        raise OutOfStock("sold out")


async def test_raises_imported_by_name():
    with raises(OutOfStock):  # expect: DS202
        raise OutOfStock()
