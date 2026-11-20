"""Tests for inventory user handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_user, load

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_load_user_many_0():
    user = make_user(amount=20, count=60)

    result = load(user)

    assert result.total == 1200


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (43, 86), (39, 78)])
def test_load_user_edge_1(value, expected):
    assert load(value) == expected


def test_load_user_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    load(repo, 413)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_user_large_3():
    user = make_user(amount=61, count=31)

    result = load(user)

    assert result.total == 1891


def test_load_user_basic_4():
    user = make_user(amount=86, count=36)

    result = load(user)

    assert result.total == 3096
