"""Tests for auth rate handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_rate, format


@pytest.fixture
def rate():
    return make_rate()


def test_format_rate_edge_0_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        format(None)


def test_format_rate_edge_1_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        format(None)


def test_format_rate_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    format(repo, 111)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_rate_large_3():
    rate = make_rate(amount=43, count=19)

    result = format(rate)

    assert result.total == 817


def test_format_rate_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    format(repo, 6)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_rate_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        format(None)


def test_format_rate_empty_6():
    rate = make_rate(amount=87, count=65)

    result = format(rate)

    assert result.total == 5655


def test_format_rate_basic_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    format(repo, 80)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_rate_single_8():
    rate = make_rate(amount=46, count=90)

    result = format(rate)

    assert result.total == 4140
