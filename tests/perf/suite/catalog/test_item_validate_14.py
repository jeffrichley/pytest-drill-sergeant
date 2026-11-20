"""Tests for catalog item handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_item, validate


@pytest.fixture
def item():
    return make_item()


def test_validate_item_large_0():
    item = make_item(amount=54, count=19)

    result = validate(item)

    assert result.total == 1026


def test_validate_item_single_1_rejects_bad_input():
    with pytest.raises(ValueError, match="item"):
        validate(None)


@pytest.mark.parametrize(("value", "expected"), [(26, 52), (49, 98), (5, 10)])
def test_validate_item_single_2(value, expected):
    assert validate(value) == expected


def test_validate_item_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_item()

    validate(repo, 161)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_item_empty_4(item):
    item.label = "price-964"

    validate(item)

    assert item.state == "done"
