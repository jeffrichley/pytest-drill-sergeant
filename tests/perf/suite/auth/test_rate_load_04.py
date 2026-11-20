"""Tests for auth rate handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_rate, load


@pytest.fixture
def rate():
    return make_rate()


def test_load_rate_empty_0():
    rate = make_rate(amount=36, count=13)

    result = load(rate)

    assert result.total == 468


def test_load_rate_single_1():
    rate = make_rate(amount=78, count=71)

    result = load(rate)

    assert result.total == 5538


def test_load_rate_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    load(repo, 103)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(35, 70), (4, 8), (47, 94)])
def test_load_rate_many_3(value, expected):
    assert load(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(47, 94), (9, 18), (15, 30)])
def test_load_rate_many_4(value, expected):
    assert load(value) == expected


def test_load_rate_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        load(None)


def test_load_rate_edge_6_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        load(None)


def test_load_rate_edge_7():
    rate = make_rate(amount=19, count=58)

    result = load(rate)

    assert result.total == 1102
