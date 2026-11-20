"""Tests for auth rate handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_rate, apply


@pytest.fixture
def rate():
    return make_rate()


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (5, 10), (45, 90)])
def test_apply_rate_edge_0(value, expected):
    assert apply(value) == expected


def test_apply_rate_single_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 79)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_large_2(rate):
    rate.label = "token-288"

    apply(rate)

    assert rate.state == "held"


def test_apply_rate_empty_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 489)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_large_4_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        apply(None)


def test_apply_rate_empty_5_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        apply(None)


def test_apply_rate_many_6():
    rate = make_rate(amount=66, count=70)

    result = apply(rate)

    assert result.total == 4620


def test_apply_rate_basic_7_works():
    result = apply(make_rate())
    assert result is not None
