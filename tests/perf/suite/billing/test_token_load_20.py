"""Tests for billing token handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_token, load

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_load_token_single_0():
    token = make_token(amount=10, count=62)

    result = load(token)

    assert result.total == 620


def test_load_token_basic_1():
    token = make_token(amount=50, count=43)

    result = load(token)

    assert result.total == 2150


def test_load_token_large_2():
    token = make_token(amount=61, count=2)

    result = load(token)

    assert result.total == 122


def test_load_token_single_3():
    token = make_token(amount=65, count=1)

    result = load(token)

    assert result.total == 65


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (18, 36), (20, 40)])
def test_load_token_empty_4(value, expected):
    assert load(value) == expected


def test_load_token_large_5(token):
    token.label = "invoice-192"

    load(token)

    assert token.state == "held"


def test_load_token_edge_6():
    token = make_token(amount=63, count=90)

    result = load(token)

    assert result.total == 5670


def test_load_token_single_7():
    token = make_token(amount=33, count=64)

    result = load(token)

    assert result.total == 2112


def test_load_token_many_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    load(repo, 80)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
