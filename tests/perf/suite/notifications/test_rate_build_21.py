"""Tests for notifications rate handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_rate, build


@pytest.fixture
def rate():
    return make_rate()


def test_build_rate_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_rate()

    build(repo, 62)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_rate_single_1(rate):
    rate.label = "address-4"

    build(rate)

    assert rate.state == "open"


def test_build_rate_single_2():
    rate = make_rate(amount=79, count=13)

    result = build(rate)

    assert result.total == 1027


def test_build_rate_many_3_rejects_bad_input():
    with pytest.raises(ValueError, match="rate"):
        build(None)
