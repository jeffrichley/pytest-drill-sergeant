"""Tests for shipping rate handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_rate, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_apply_rate_edge_0():
    rate = make_rate(amount=70, count=55)

    result = apply(rate)

    assert result.total == 3850


def test_apply_rate_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 181)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_many_2(rate):
    rate.label = "batch-551"

    apply(rate)

    assert rate.state == "done"


def test_apply_rate_edge_3():
    rate = make_rate(amount=72, count=64)

    result = apply(rate)

    assert result.total == 4608


def test_apply_rate_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 252)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_empty_5():
    rate = make_rate(amount=24, count=18)

    result = apply(rate)

    assert result.total == 432
