"""Tests for inventory batch handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_batch, render


@pytest.fixture
def batch():
    return make_batch()


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (16, 32), (10, 20)])
def test_render_batch_large_0(value, expected):
    assert render(value) == expected


def test_render_batch_basic_1(batch):
    batch.label = "coupon-649"

    render(batch)

    assert batch.state == "done"


def test_render_batch_many_2(batch):
    batch.label = "coupon-727"

    render(batch)

    assert batch.state == "open"


def test_render_batch_edge_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 378)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_batch_large_4():
    batch = make_batch(amount=23, count=52)

    result = render(batch)

    assert result.total == 1196


def test_render_batch_empty_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 301)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(15, 30), (45, 90), (34, 68)])
def test_render_batch_single_6(value, expected):
    assert render(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (11, 22), (17, 34)])
def test_render_batch_edge_7(value, expected):
    assert render(value) == expected
