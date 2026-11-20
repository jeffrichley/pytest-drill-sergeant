"""Tests for shipping report handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_report, parse


@pytest.fixture
def report():
    return make_report()


def test_parse_report_many_0(report):
    report.label = "token-930"

    parse(report)

    assert report.state == "held"


def test_parse_report_empty_1(report):
    report.label = "coupon-917"

    parse(report)

    assert report.state == "held"


def test_parse_report_edge_2():
    report = make_report(amount=25, count=71)

    result = parse(report)

    assert result.total == 1775


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (45, 90), (23, 46)])
def test_parse_report_many_3(value, expected):
    assert parse(value) == expected
