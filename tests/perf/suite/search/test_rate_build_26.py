"""Tests for search rate handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_rate, build

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (27, 54), (26, 52)])
def test_build_rate_edge_0(value, expected):
    assert build(value) == expected


def test_build_rate_large_1(rate):
    rate.label = "event-210"

    build(rate)

    assert rate.state == "open"


def test_build_rate_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 430)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_basic_3():
    rate = make_rate(amount=67, count=59)

    result = build(rate)

    assert result.total == 3953


def test_build_rate_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 53)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_many_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 91)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_single_6():
    rate = make_rate(amount=95, count=76)

    result = build(rate)

    assert result.total == 7220


def test_build_rate_single_7(rate):
    rate.label = "token-31"

    build(rate)

    assert rate.state == "done"
