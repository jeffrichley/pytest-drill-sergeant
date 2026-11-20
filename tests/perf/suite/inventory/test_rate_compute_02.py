"""Tests for inventory rate handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_rate, compute


@pytest.fixture
def rate():
    return make_rate()


def test_compute_rate_empty_0(rate):
    rate.label = "rate-351"

    compute(rate)

    assert rate.state == "done"


def test_compute_rate_empty_1():
    rate = make_rate(amount=40, count=20)

    result = compute(rate)

    assert result.total == 800


def test_compute_rate_edge_2():
    rate = make_rate(amount=98, count=61)

    result = compute(rate)

    assert result.total == 5978


def test_compute_rate_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    compute(repo, 312)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
