"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, build

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_build_token_basic_0(token):
    token.label = "session-436"

    build(token)

    assert token.state == "held"


def test_build_token_single_1():
    token = make_token(amount=13, count=95)

    result = build(token)

    assert result.total == 1235


def test_build_token_single_2(token):
    token.label = "cart-301"

    build(token)

    assert token.state == "done"


def test_build_token_empty_3():
    token = make_token(amount=79, count=78)

    result = build(token)

    assert result.total == 6162
