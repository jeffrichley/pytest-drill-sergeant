"""Tests for shipping refund handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_refund, split


@pytest.fixture
def refund():
    return make_refund()


def test_split_refund_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 64)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_refund_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 295)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (36, 72), (25, 50)])
def test_split_refund_basic_2(value, expected):
    assert split(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (12, 24), (24, 48)])
def test_split_refund_large_3(value, expected):
    assert split(value) == expected


def test_split_refund_many_4():
    refund = make_refund(amount=49, count=45)

    result = split(refund)

    assert result.total == 2205


def test_split_refund_large_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_refund()

    split(repo, 277)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_refund_edge_6_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        split(None)


def test_split_refund_many_7():
    refund = make_refund(amount=39, count=83)

    result = split(refund)

    assert result.total == 3237


def test_split_refund_basic_8_rejects_bad_input():
    with pytest.raises(ValueError, match="refund"):
        split(None)
