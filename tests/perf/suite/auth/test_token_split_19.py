"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, split

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_split_token_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    split(repo, 84)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_token_basic_1():
    token = make_token(amount=12, count=86)

    result = split(token)

    assert result.total == 1032


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (23, 46), (4, 8)])
def test_split_token_large_2(value, expected):
    assert split(value) == expected


def test_split_token_large_3(token):
    token.label = "token-766"

    split(token)

    assert token.state == "held"


def test_split_token_basic_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    split(repo, 354)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (12, 24), (18, 36)])
def test_split_token_many_5(value, expected):
    assert split(value) == expected


def test_split_token_many_6(token):
    token.label = "invoice-601"

    split(token)

    assert token.state == "done"


def test_split_token_basic_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    split(repo, 337)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_token_large_8():
    token = make_token(amount=89, count=9)

    result = split(token)

    assert result.total == 801
