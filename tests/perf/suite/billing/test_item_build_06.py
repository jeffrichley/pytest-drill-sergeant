"""Tests for billing item handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_item, build


@pytest.fixture
def item():
    return make_item()


def test_build_item_empty_0(item):
    item.label = "item-563"

    build(item)

    assert item.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (13, 26), (6, 12)])
def test_build_item_edge_1(value, expected):
    assert build(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(18, 36), (30, 60), (42, 84)])
def test_build_item_many_2(value, expected):
    assert build(value) == expected


def test_build_item_empty_3(item):
    item.label = "session-903"

    build(item)

    assert item.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(14, 28), (36, 72), (10, 20)])
def test_build_item_many_4(value, expected):
    assert build(value) == expected


def test_build_item_basic_5(item):
    item.label = "session-431"

    build(item)

    assert item.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(21, 42), (25, 50), (7, 14)])
def test_build_item_empty_6(value, expected):
    assert build(value) == expected


def test_build_item_edge_7():
    item = make_item(amount=71, count=78)

    result = build(item)

    assert result.total == 5538


def test_build_item_single_8():
    item = make_item(amount=96, count=75)

    result = build(item)

    assert result.total == 7200
