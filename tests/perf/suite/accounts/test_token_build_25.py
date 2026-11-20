"""Tests for accounts token handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_token, build

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_build_token_basic_0():
    token = make_token(amount=81, count=58)

    result = build(token)

    assert result.total == 4698


def test_build_token_basic_1():
    token = make_token(amount=1, count=14)

    result = build(token)

    assert result.total == 14


def test_build_token_empty_2(token):
    token.label = "user-880"

    build(token)

    assert token.state == "done"


def test_build_token_edge_3():
    token = make_token(amount=92, count=73)

    result = build(token)

    assert result.total == 6716


def test_build_token_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    build(repo, 33)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
