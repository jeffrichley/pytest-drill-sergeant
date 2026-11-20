"""Tests for notifications report handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_report, validate

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_validate_report_empty_0():
    report = make_report(amount=40, count=66)

    result = validate(report)

    assert result.total == 2640


def test_validate_report_empty_1_works():
    result = validate(make_report())
    assert result is not None


def test_validate_report_large_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    validate(repo, 125)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_report_edge_3():
    report = make_report(amount=84, count=36)

    result = validate(report)

    assert result.total == 3024


@pytest.mark.parametrize(("value", "expected"), [(27, 54), (25, 50), (7, 14)])
def test_validate_report_edge_4(value, expected):
    assert validate(value) == expected
