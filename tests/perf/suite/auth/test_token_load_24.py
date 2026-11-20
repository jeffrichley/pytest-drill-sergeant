"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, load

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (32, 64), (35, 70)])
def test_load_token_single_0(value, expected):
    assert load(value) == expected


def test_load_token_edge_1():
    token = make_token(amount=10, count=52)

    result = load(token)

    assert result.total == 520


def test_load_token_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    load(repo, 299)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_token_empty_3():
    token = make_token(amount=21, count=93)

    result = load(token)

    assert result.total == 1953
