"""Tests for auth token handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_token, compute


@pytest.fixture
def token():
    return make_token()


def test_compute_token_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    compute(repo, 107)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_token_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    compute(repo, 214)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_token_basic_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    compute(repo, 472)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_compute_token_large_3():
    token = make_token(amount=29, count=40)

    result = compute(token)

    assert result.total == 1160


def test_compute_token_empty_4_rejects_bad_input():
    with pytest.raises(ValueError, match="token"):
        compute(None)


def test_compute_token_empty_5():
    token = make_token(amount=44, count=33)

    result = compute(token)

    assert result.total == 1452
