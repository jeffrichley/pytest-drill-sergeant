"""Near-miss: the mock setup lives in a fixture, which is no test. Analysed, never
run."""

from unittest import mock

import pytest
from shop import Checkout, Gateway, Repo

pytestmark = pytest.mark.unit


@pytest.fixture
def repo():
    repo = mock.create_autospec(Repo, instance=True)
    repo.find_cart.return_value = {"id": 7, "lines": [1, 2]}
    repo.find_customer.return_value = {"id": 1, "tier": "gold"}
    repo.find_prices.return_value = {1: 1000, 2: 500}
    repo.reserve.return_value = True
    repo.release.side_effect = None
    repo.audit.return_value = None
    repo.lock.return_value = True
    repo.unlock.return_value = True
    repo.ping.return_value = "pong"
    repo.version = 3
    return repo


def test_checkout_total(repo):
    gateway = mock.create_autospec(Gateway, instance=True)
    gateway.capture.return_value = {"status": "ok"}
    assert Checkout(repo, gateway).run(cart_id=7).total == 1350
