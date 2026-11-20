"""Tests for reports token handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_token, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def token():
    return make_token()


def test_resolve_token_empty_0():
    token = make_token(amount=30, count=88)

    result = resolve(token)

    assert result.total == 2640


def test_resolve_token_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    resolve(repo, 172)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_token_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_token()

    resolve(repo, 396)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(40, 80), (39, 78), (22, 44)])
def test_resolve_token_single_3(value, expected):
    assert resolve(value) == expected


def test_resolve_token_large_4():
    token = make_token(amount=54, count=37)

    result = resolve(token)

    assert result.total == 1998


@pytest.mark.parametrize(("value", "expected"), [(22, 44), (3, 6), (44, 88)])
def test_resolve_token_single_5(value, expected):
    assert resolve(value) == expected
