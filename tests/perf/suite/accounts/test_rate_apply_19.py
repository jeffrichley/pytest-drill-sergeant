"""Tests for accounts rate handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_rate, apply


@pytest.fixture
def rate():
    return make_rate()


def test_apply_rate_edge_0():
    rate = make_rate(amount=23, count=43)

    result = apply(rate)

    assert result.total == 989


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (38, 76), (15, 30)])
def test_apply_rate_many_1(value, expected):
    assert apply(value) == expected


def test_apply_rate_many_2_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        apply(None)


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (21, 42), (27, 54)])
def test_apply_rate_large_3(value, expected):
    assert apply(value) == expected


def test_apply_rate_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    apply(repo, 295)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_rate_empty_5():
    rate = make_rate(amount=1, count=54)

    result = apply(rate)

    assert result.total == 54


def test_apply_rate_single_6_works():
    result = apply(make_rate())
    assert result is not None
