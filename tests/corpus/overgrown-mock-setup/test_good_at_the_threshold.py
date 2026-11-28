"""Near-miss: exactly five mock targets, the default threshold. Reading a mock, its
data attributes, a `configure_mock` of plain values and calling the code under test
aren't setup. Analysed, never run."""

from unittest import mock

import pytest
from shop import Checkout, Gateway, Repo

pytestmark = pytest.mark.unit


def test_checkout_total():
    repo = mock.create_autospec(Repo, instance=True)
    gateway = mock.create_autospec(Gateway, instance=True)
    repo.find_cart.return_value = {"id": 7, "lines": [1, 2]}
    repo.find_prices.return_value = {1: 1000, 2: 500}
    gateway.capture.side_effect = [{"status": "ok"}]
    gateway.currency = "EUR"
    gateway.limits["per_day"] = 10_000
    gateway.configure_mock(fee=0, region="eu")
    capture = gateway.capture
    receipt = Checkout(repo, gateway).run(cart_id=7)
    assert receipt.total == 1350
    assert capture.call_count == 1
