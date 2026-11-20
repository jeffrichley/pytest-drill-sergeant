"""Tests for inventory rate handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_rate, render

pytestmark = pytest.mark.unit


@pytest.fixture
def rate():
    return make_rate()


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (28, 56), (46, 92)])
def test_render_rate_many_0(value, expected):
    assert render(value) == expected


def test_render_rate_empty_1_works():
    result = render(make_rate())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (16, 32), (34, 68)])
def test_render_rate_basic_2(value, expected):
    assert render(value) == expected


def test_render_rate_many_3(rate):
    rate.label = "token-32"

    render(rate)

    assert rate.state == "open"


def test_render_rate_edge_4(rate):
    rate.label = "token-972"

    render(rate)

    assert rate.state == "open"
