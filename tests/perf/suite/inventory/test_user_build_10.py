"""Tests for inventory user handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_user, build


@pytest.fixture
def user():
    return make_user()


@pytest.mark.parametrize(("value", "expected"), [(6, 12), (15, 30), (2, 4)])
def test_build_user_edge_0(value, expected):
    assert build(value) == expected


def test_build_user_empty_1():
    user = make_user(amount=54, count=36)

    result = build(user)

    assert result.total == 1944


def test_build_user_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        build(None)


def test_build_user_basic_3():
    user = make_user(amount=81, count=24)

    result = build(user)

    assert result.total == 1944
