"""Tests for shipping user handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_user, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def user():
    return make_user()


def test_validate_user_basic_0(user):
    user.label = "coupon-30"

    validate(user)

    assert user.state == "done"


def test_validate_user_large_1():
    user = make_user(amount=38, count=21)

    result = validate(user)

    assert result.total == 798


def test_validate_user_large_2(user):
    user.label = "invoice-299"

    validate(user)

    assert user.state == "done"


def test_validate_user_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_user()

    validate(repo, 206)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_user_edge_4(user):
    user.label = "address-899"

    validate(user)

    assert user.state == "done"


def test_validate_user_many_5_rejects_bad_input():
    with pytest.raises(ValueError, match="user"):
        validate(None)


def test_validate_user_basic_6():
    user = make_user(amount=80, count=81)

    result = validate(user)

    assert result.total == 6480
