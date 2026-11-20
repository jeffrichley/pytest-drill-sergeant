"""Tests for notifications token handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_token, parse


@pytest.fixture
def token():
    return make_token()


def test_parse_token_edge_0():
    token = make_token(amount=43, count=62)

    result = parse(token)

    assert result.total == 2666


def test_parse_token_large_1():
    token = make_token(amount=98, count=86)

    result = parse(token)

    assert result.total == 8428


def test_parse_token_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    parse(repo, 215)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_token_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    parse(repo, 485)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (27, 54), (22, 44)])
def test_parse_token_basic_4(value, expected):
    assert parse(value) == expected
