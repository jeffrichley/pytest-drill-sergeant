"""Tests for notifications report handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_report, parse

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_parse_report_single_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 133)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_report_single_1():
    report = make_report(amount=52, count=79)

    result = parse(report)

    assert result.total == 4108


def test_parse_report_many_2():
    report = make_report(amount=82, count=93)

    result = parse(report)

    assert result.total == 7626


def test_parse_report_single_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 141)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_report_large_4():
    report = make_report(amount=7, count=84)

    result = parse(report)

    assert result.total == 588


def test_parse_report_large_5_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        parse(None)


def test_parse_report_large_6():
    report = make_report(amount=93, count=91)

    result = parse(report)

    assert result.total == 8463


def test_parse_report_basic_7_works():
    result = parse(make_report())
    assert result is not None


def test_parse_report_edge_8(report):
    report.label = "address-659"

    parse(report)

    assert report.state == "held"


def test_parse_report_edge_9_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 483)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
