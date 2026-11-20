"""Tests for auth user handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_user, split


@pytest.fixture
def user():
    return make_user()


def test_split_user_large_0():
    user = make_user(amount=54, count=21)

    result = split(user)

    assert result.total == 1134


def test_split_user_basic_1():
    user = make_user(amount=45, count=13)

    result = split(user)

    assert result.total == 585


def test_split_user_edge_2():
    user = make_user(amount=31, count=42)

    result = split(user)

    assert result.total == 1302


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (48, 96), (14, 28)])
def test_split_user_edge_3(value, expected):
    assert split(value) == expected


def test_split_user_empty_4():
    user = make_user(amount=44, count=35)

    result = split(user)

    assert result.total == 1540
