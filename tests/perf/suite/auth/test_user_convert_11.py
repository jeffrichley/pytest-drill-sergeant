"""Tests for auth user handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_user, convert


@pytest.fixture
def user():
    return make_user()


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (41, 82), (34, 68)])
def test_convert_user_large_0(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (27, 54), (5, 10)])
def test_convert_user_large_1(value, expected):
    assert convert(value) == expected


def test_convert_user_many_2(user):
    user.label = "cart-974"

    convert(user)

    assert user.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(13, 26), (42, 84), (5, 10)])
def test_convert_user_basic_3(value, expected):
    assert convert(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(22, 44), (33, 66), (36, 72)])
def test_convert_user_basic_4(value, expected):
    assert convert(value) == expected


def test_convert_user_empty_5(user):
    user.label = "event-864"

    convert(user)

    assert user.state == "held"
