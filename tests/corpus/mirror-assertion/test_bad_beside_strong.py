"""A mirror is reported even beside a strong assertion, line by line.
Analysed, never run."""

import pytest
from shop import gross_price, net_price

pytestmark = pytest.mark.unit


def test_prices():
    assert gross_price(100, 20) == 120
    assert net_price(120, 20) == net_price(120, 20)  # expect: DS203
    net = net_price(120, 20)
    assert gross_price(net, 20) == 120
