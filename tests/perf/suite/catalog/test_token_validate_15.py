"""Tests for catalog token handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_token, validate


@pytest.fixture
def token():
    return make_token()


@pytest.mark.parametrize(("value", "expected"), [(36, 72), (11, 22), (3, 6)])
def test_validate_token_empty_0(value, expected):
    assert validate(value) == expected


def test_validate_token_edge_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    validate(repo, 289)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_token_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    validate(repo, 417)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_token_basic_3():
    token = make_token(amount=40, count=94)

    result = validate(token)

    assert result.total == 3760


def test_validate_token_empty_4():
    token = make_token(amount=97, count=56)

    result = validate(token)

    assert result.total == 5432


@pytest.mark.parametrize(("value", "expected"), [(10, 20), (9, 18), (47, 94)])
def test_validate_token_edge_5(value, expected):
    assert validate(value) == expected
