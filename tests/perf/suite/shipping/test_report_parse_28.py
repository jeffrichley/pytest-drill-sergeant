"""Tests for shipping report handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_report, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_parse_report_edge_0():
    report = make_report(amount=95, count=46)

    result = parse(report)

    assert result.total == 4370


def test_parse_report_basic_1():
    report = make_report(amount=17, count=63)

    result = parse(report)

    assert result.total == 1071


def test_parse_report_basic_2_works():
    result = parse(make_report())
    assert result is not None


def test_parse_report_large_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 403)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_report_edge_4():
    report = make_report(amount=11, count=43)

    result = parse(report)

    assert result.total == 473


@pytest.mark.parametrize(("value", "expected"), [(23, 46), (49, 98), (14, 28)])
def test_parse_report_large_5(value, expected):
    assert parse(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (41, 82), (21, 42)])
def test_parse_report_many_6(value, expected):
    assert parse(value) == expected
