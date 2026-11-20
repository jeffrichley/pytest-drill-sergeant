"""Tests for inventory report handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_report, convert


@pytest.fixture
def report():
    return make_report()


def test_convert_report_many_0():
    report = make_report(amount=26, count=11)

    result = convert(report)

    assert result.total == 286


def test_convert_report_empty_1(report):
    report.label = "batch-336"

    convert(report)

    assert report.state == "held"


def test_convert_report_large_2_works():
    result = convert(make_report())
    assert result is not None


def test_convert_report_many_3(report):
    report.label = "user-256"

    convert(report)

    assert report.state == "held"


def test_convert_report_single_4():
    report = make_report(amount=53, count=48)

    result = convert(report)

    assert result.total == 2544


def test_convert_report_many_5():
    report = make_report(amount=27, count=74)

    result = convert(report)

    assert result.total == 1998


@pytest.mark.parametrize(("value", "expected"), [(25, 50), (1, 2), (5, 10)])
def test_convert_report_many_6(value, expected):
    assert convert(value) == expected


def test_convert_report_basic_7():
    report = make_report(amount=92, count=43)

    result = convert(report)

    assert result.total == 3956
