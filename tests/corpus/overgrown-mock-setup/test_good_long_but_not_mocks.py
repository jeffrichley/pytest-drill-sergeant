"""Near-misses: long setup on fakes and on a fixture named like a mock, whose kind
the file never shows. Analysed, never run."""

import pytest
from shop import Checkout, FakeGateway, FakeRepo

pytestmark = pytest.mark.unit


def test_checkout_with_fakes():
    repo = FakeRepo()
    gateway = FakeGateway()
    repo.carts[7] = {"id": 7, "lines": [1, 2]}
    repo.customers[1] = {"id": 1, "tier": "gold"}
    repo.prices[1] = 1000
    repo.prices[2] = 500
    repo.stock[1] = 3
    repo.stock[2] = 3
    gateway.currency = "EUR"
    gateway.limit = 10_000
    gateway.accepts = {"visa"}
    gateway.fee = 0
    assert Checkout(repo, gateway).run(cart_id=7).total == 1350


def test_fixture_named_like_a_mock(mock_repo, mock_gateway):
    mock_repo.find_cart.return_value = {"id": 7, "lines": [1, 2]}
    mock_repo.find_customer.return_value = {"id": 1, "tier": "gold"}
    mock_repo.find_prices.return_value = {1: 1000, 2: 500}
    mock_repo.reserve.return_value = True
    mock_repo.release.side_effect = None
    mock_gateway.authorize.return_value = "auth-1"
    mock_gateway.capture.return_value = {"status": "ok"}
    mock_gateway.currency = "EUR"
    mock_gateway.limit = 10_000
    mock_gateway.fee = 0
    mock_gateway.accepts = {"visa"}
    assert Checkout(mock_repo, mock_gateway).run(cart_id=7).total == 1350
