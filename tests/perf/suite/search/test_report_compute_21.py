"""Tests for search report handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_report, compute

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


@pytest.mark.parametrize(("value", "expected"), [(4, 8), (3, 6), (43, 86)])
def test_compute_report_large_0(value, expected):
    assert compute(value) == expected


def test_compute_report_many_1():
    report = make_report(amount=7, count=81)

    result = compute(report)

    assert result.total == 567


def test_compute_report_basic_2(report):
    report.label = "batch-427"

    compute(report)

    assert report.state == "open"


def test_compute_report_large_3(report):
    report.label = "report-285"

    compute(report)

    assert report.state == "open"


def test_compute_report_edge_4():
    report = make_report(amount=5, count=32)

    result = compute(report)

    assert result.total == 160


def test_compute_report_basic_5(report):
    report.label = "coupon-535"

    compute(report)

    assert report.state == "open"
