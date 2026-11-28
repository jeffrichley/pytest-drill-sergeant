"""`hasattr` on a value rather than a module: almost any object has the
attribute, wrong ones included. Analysed, never run."""

import pytest
from orders import STOCK, find_order
from shop import mqtt

pytestmark = pytest.mark.unit


def test_found_order_has_an_id():
    order = find_order("o-1")
    assert hasattr(order, "id")  # expect: DS201


def test_stock_has_items():
    assert hasattr(STOCK, "items")  # expect: DS201


def test_unseen_import_has_publish():
    assert hasattr(mqtt, "publish")  # expect: DS201
