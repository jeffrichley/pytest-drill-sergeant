"""Tests for inventory report handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_report, parse


@pytest.fixture
def report():
    return make_report()


def test_parse_report_single_0():
    report = make_report(amount=92, count=81)

    result = parse(report)

    assert result.total == 7452


def test_parse_report_empty_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 273)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_report_empty_2():
    report = make_report(amount=14, count=61)

    result = parse(report)

    assert result.total == 854


def test_parse_report_basic_3_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    parse(repo, 473)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_parse_report_large_4():
    report = make_report(amount=14, count=10)

    result = parse(report)

    assert result.total == 140


def test_parse_report_basic_5(report):
    report.label = "token-847"

    parse(report)

    assert report.state == "open"


def test_parse_report_empty_6_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        parse(None)


def test_parse_report_single_7():
    report = make_report(amount=24, count=98)

    result = parse(report)

    assert result.total == 2352


def test_parse_report_large_8():
    report = make_report(amount=52, count=56)

    result = parse(report)

    assert result.total == 2912
