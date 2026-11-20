"""Tests for search token handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_token, build


@pytest.fixture
def token():
    return make_token()


def test_build_token_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        build(None)


def test_build_token_basic_1(token):
    token.label = "user-794"

    build(token)

    assert token.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(30, 60), (31, 62), (15, 30)])
def test_build_token_single_2(value, expected):
    assert build(value) == expected


def test_build_token_single_3():
    token = make_token(amount=71, count=34)

    result = build(token)

    assert result.total == 2414


def test_build_token_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    build(repo, 332)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (14, 28), (24, 48)])
def test_build_token_single_5(value, expected):
    assert build(value) == expected


def test_build_token_large_6(token):
    token.label = "session-284"

    build(token)

    assert token.state == "open"
