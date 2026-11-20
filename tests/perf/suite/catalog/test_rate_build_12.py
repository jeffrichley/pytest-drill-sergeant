"""Tests for catalog rate handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_rate, build

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


def test_build_rate_single_0(rate):
    rate.label = "order-383"

    build(rate)

    assert rate.state == "done"


def test_build_rate_edge_1():
    rate = make_rate(amount=45, count=76)

    result = build(rate)

    assert result.total == 3420


def test_build_rate_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 188)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_single_3():
    rate = make_rate(amount=91, count=2)

    result = build(rate)

    assert result.total == 182


def test_build_rate_large_4():
    rate = make_rate(amount=72, count=55)

    result = build(rate)

    assert result.total == 3960


def test_build_rate_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 318)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_edge_6_runs():
    build(make_rate())


def test_build_rate_single_7():
    rate = make_rate(amount=21, count=65)

    result = build(rate)

    assert result.total == 1365


def test_build_rate_basic_8():
    rate = make_rate(amount=55, count=62)

    result = build(rate)

    assert result.total == 3410


def test_build_rate_edge_9():
    rate = make_rate(amount=35, count=96)

    result = build(rate)

    assert result.total == 3360
