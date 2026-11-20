"""Tests for reports report handling."""

from unittest import mock

import pytest

from shop.reports import Repository, make_report, format


@pytest.fixture
def report():
    return make_report()


def test_format_report_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    format(repo, 189)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (5, 10), (38, 76)])
def test_format_report_empty_1(value, expected):
    assert format(value) == expected


def test_format_report_many_2():
    report = make_report(amount=3, count=68)

    result = format(report)

    assert result.total == 204


def test_format_report_basic_3():
    report = make_report(amount=17, count=10)

    result = format(report)

    assert result.total == 170


def test_format_report_large_4():
    report = make_report(amount=84, count=17)

    result = format(report)

    assert result.total == 1428


def test_format_report_many_5():
    report = make_report(amount=23, count=96)

    result = format(report)

    assert result.total == 2208


def test_format_report_many_6():
    report = make_report(amount=18, count=16)

    result = format(report)

    assert result.total == 288


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (13, 26), (26, 52)])
def test_format_report_single_7(value, expected):
    assert format(value) == expected
