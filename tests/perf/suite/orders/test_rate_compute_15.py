"""Tests for orders rate handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_rate, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_compute_rate_basic_0():
    rate = make_rate(amount=73, count=26)

    result = compute(rate)

    assert result.total == 1898


def test_compute_rate_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    compute(repo, 229)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_rate_single_2(rate):
    rate.label = "order-760"

    compute(rate)

    assert rate.state == "held"


def test_compute_rate_edge_3():
    rate = make_rate(amount=31, count=87)

    result = compute(rate)

    assert result.total == 2697


def test_compute_rate_many_4(rate):
    rate.label = "batch-812"

    compute(rate)

    assert rate.state == "held"
