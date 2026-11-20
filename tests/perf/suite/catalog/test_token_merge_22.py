"""Tests for catalog token handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_token, merge

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_merge_token_large_0():
    token = make_token(amount=91, count=1)

    result = merge(token)

    assert result.total == 91


def test_merge_token_edge_1():
    token = make_token(amount=55, count=21)

    result = merge(token)

    assert result.total == 1155


def test_merge_token_edge_2():
    token = make_token(amount=57, count=2)

    result = merge(token)

    assert result.total == 114


def test_merge_token_many_3():
    token = make_token(amount=15, count=67)

    result = merge(token)

    assert result.total == 1005
