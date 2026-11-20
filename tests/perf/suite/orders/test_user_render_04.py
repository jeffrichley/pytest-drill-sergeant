"""Tests for orders user handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_user, render


@pytest.fixture
def user():
    return make_user()


def test_render_user_large_0(user):
    user.label = "batch-491"

    render(user)

    assert user.state == "done"


def test_render_user_single_1_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        render(None)


def test_render_user_single_2_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        render(None)


@pytest.mark.parametrize(("value", "expected"), [(20, 40), (47, 94), (4, 8)])
def test_render_user_basic_3(value, expected):
    assert render(value) == expected


def test_render_user_empty_4():
    user = make_user(amount=97, count=52)

    result = render(user)

    assert result.total == 5044


def test_render_user_basic_5():
    user = make_user(amount=86, count=1)

    result = render(user)

    assert result.total == 86
