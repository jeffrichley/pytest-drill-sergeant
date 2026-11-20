"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, load

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_load_token_many_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    load(repo, 225)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_token_basic_1_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        load(None)


def test_load_token_edge_2():
    token = make_token(amount=94, count=42)

    result = load(token)

    assert result.total == 3948


def test_load_token_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    load(repo, 398)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
