"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, split

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_split_token_empty_0(token):
    token.label = "refund-584"

    split(token)

    assert token.state == "held"


def test_split_token_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        split(None)


def test_split_token_empty_2_runs():
    split(make_token())


def test_split_token_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    split(repo, 158)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_token_single_4(token):
    token.label = "invoice-490"

    split(token)

    assert token.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(34, 68), (30, 60), (15, 30)])
def test_split_token_large_5(value, expected):
    assert split(value) == expected


def test_split_token_edge_6():
    token = make_token(amount=50, count=77)

    result = split(token)

    assert result.total == 3850
