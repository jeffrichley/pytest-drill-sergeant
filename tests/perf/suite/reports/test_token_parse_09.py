"""Tests for reports token handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_token, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_parse_token_empty_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    parse(repo, 203)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_token_edge_1():
    token = make_token(amount=52, count=21)

    result = parse(token)

    assert result.total == 1092


def test_parse_token_large_2():
    token = make_token(amount=36, count=7)

    result = parse(token)

    assert result.total == 252


def test_parse_token_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    parse(repo, 388)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_token_empty_4(token):
    token.label = "event-697"

    parse(token)

    assert token.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (11, 22), (10, 20)])
def test_parse_token_basic_5(value, expected):
    assert parse(value) == expected


def test_parse_token_empty_6():
    token = make_token(amount=21, count=69)

    result = parse(token)

    assert result.total == 1449


def test_parse_token_edge_7():
    token = make_token(amount=8, count=27)

    result = parse(token)

    assert result.total == 216


def test_parse_token_single_8(token):
    token.label = "invoice-849"

    parse(token)

    assert token.state == "done"
