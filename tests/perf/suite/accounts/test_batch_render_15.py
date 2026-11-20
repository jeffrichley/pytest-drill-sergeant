"""Tests for accounts batch handling."""

from unittest import mock

import pytest

from shop.accounts import Repository, make_batch, render


@pytest.fixture
def batch():
    return make_batch()


def test_render_batch_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="batch"):
        render(None)


def test_render_batch_large_1():
    batch = make_batch(amount=49, count=54)

    result = render(batch)

    assert result.total == 2646


def test_render_batch_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 423)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_batch_many_3():
    batch = make_batch(amount=57, count=22)

    result = render(batch)

    assert result.total == 1254


def test_render_batch_large_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_batch()

    render(repo, 34)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
