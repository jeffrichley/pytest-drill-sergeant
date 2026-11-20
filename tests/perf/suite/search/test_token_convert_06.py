"""Tests for search token handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_token, convert

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_convert_token_empty_0():
    token = make_token(amount=88, count=84)

    result = convert(token)

    assert result.total == 7392


def test_convert_token_empty_1_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        convert(None)


def test_convert_token_empty_2():
    token = make_token(amount=37, count=34)

    result = convert(token)

    assert result.total == 1258


def test_convert_token_single_3_runs():
    convert(make_token())


def test_convert_token_edge_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    convert(repo, 349)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
