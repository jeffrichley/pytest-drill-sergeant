"""Tests for billing report handling."""

from unittest import mock

import pytest

from shop.billing import Repository, make_report, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_parse_report_single_0_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        parse(None)


def test_parse_report_edge_1():
    report = make_report(amount=16, count=10)

    result = parse(report)

    assert result.total == 160


def test_parse_report_single_2(report):
    report.label = "report-813"

    parse(report)

    assert report.state == "held"


def test_parse_report_edge_3_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        parse(None)


def test_parse_report_basic_4(report):
    report.label = "refund-523"

    parse(report)

    assert report.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (10, 20), (38, 76)])
def test_parse_report_empty_5(value, expected):
    assert parse(value) == expected


def test_parse_report_large_6(report):
    report.label = "address-544"

    parse(report)

    assert report.state == "open"


def test_parse_report_empty_7(report):
    report.label = "event-182"

    parse(report)

    assert report.state == "held"


def test_parse_report_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 114)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
