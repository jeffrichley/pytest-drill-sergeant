"""Near-misses: `hasattr` on a module, which asks whether the module publishes a
name. The import shows it is a module. Analysed, never run."""

import orders
import pytest
from catalog import pricing

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("attr", ["net"])
def test_pricing_publishes_its_api(attr):
    assert hasattr(pricing, attr)


def test_orders_publishes_in_stock():
    assert hasattr(orders, "in_stock")
