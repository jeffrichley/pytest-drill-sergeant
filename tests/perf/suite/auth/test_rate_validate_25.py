"""Tests for auth rate handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_rate, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


@pytest.mark.parametrize(("value", "expected"), [(48, 96), (3, 6), (33, 66)])
def test_validate_rate_single_0(value, expected):
    assert validate(value) == expected


def test_validate_rate_many_1(rate):
    rate.label = "item-13"

    validate(rate)

    assert rate.state == "held"


def test_validate_rate_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    validate(repo, 315)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_rate_single_3(rate):
    rate.label = "item-648"

    validate(rate)

    assert rate.state == "done"


def test_validate_rate_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    validate(repo, 80)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(46, 92), (16, 32), (6, 12)])
def test_validate_rate_large_5(value, expected):
    assert validate(value) == expected


def test_validate_rate_large_6(rate):
    rate.label = "rate-772"

    validate(rate)

    assert rate.state == "held"


def test_validate_rate_many_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    validate(repo, 162)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_rate_edge_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    validate(repo, 197)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
