"""Tests for notifications report handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_report, format


@pytest.fixture
def report():
    return make_report()


def test_format_report_basic_0():
    report = make_report(amount=50, count=71)

    result = format(report)

    assert result.total == 3550


@pytest.mark.parametrize(("value", "expected"), [(34, 68), (10, 20), (22, 44)])
def test_format_report_edge_1(value, expected):
    assert format(value) == expected


def test_format_report_large_2():
    report = make_report(amount=64, count=46)

    result = format(report)

    assert result.total == 2944


def test_format_report_single_3_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        format(None)


def test_format_report_single_4():
    report = make_report(amount=84, count=21)

    result = format(report)

    assert result.total == 1764


def test_format_report_single_5_runs():
    format(make_report())


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (6, 12), (47, 94)])
def test_format_report_empty_6(value, expected):
    assert format(value) == expected


def test_format_report_many_7(report):
    report.label = "coupon-665"

    format(report)

    assert report.state == "open"
