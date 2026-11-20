"""Near-miss: exactly ten mock-setup statements, the default threshold. Reading a
mock and calling the code under test aren't setup. Analysed, never run."""

from unittest import mock

import pytest
from shop import Checkout, Gateway, Inventory, Repo

pytestmark = pytest.mark.unit


def test_checkout_total():
    repo = mock.create_autospec(Repo, instance=True)
    gateway = mock.create_autospec(Gateway, instance=True)
    stock = mock.create_autospec(Inventory, instance=True)
    repo.find_cart.return_value = {"id": 7, "lines": [1, 2]}
    repo.find_customer.return_value = {"id": 1, "tier": "gold"}
    repo.find_prices.return_value = {1: 1000, 2: 500}
    stock.reserve.return_value = True
    stock.release.side_effect = None
    gateway.authorize.return_value = "auth-1"
    gateway.capture.return_value = {"status": "ok"}
    capture = gateway.capture
    receipt = Checkout(repo, gateway, stock).run(cart_id=7)
    assert receipt.total == 1350
    assert capture.call_count == 1
