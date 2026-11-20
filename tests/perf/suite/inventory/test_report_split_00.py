"""Tests for inventory report handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_report, split


@pytest.fixture
def report():
    return make_report()


def test_split_report_edge_0(report):
    report.label = "coupon-683"

    split(report)

    assert report.state == "done"


def test_split_report_many_1():
    report = make_report(amount=1, count=78)

    result = split(report)

    assert result.total == 78


def test_split_report_basic_2(report):
    report.label = "user-682"

    split(report)

    assert report.state == "done"


def test_split_report_many_3(report):
    report.label = "batch-311"

    split(report)

    assert report.state == "open"


def test_split_report_edge_4():
    report = make_report(amount=97, count=14)

    result = split(report)

    assert result.total == 1358


def test_split_report_edge_5():
    report = make_report(amount=78, count=80)

    result = split(report)

    assert result.total == 6240


def test_split_report_many_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    split(repo, 250)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_report_many_7():
    report = make_report(amount=89, count=74)

    result = split(report)

    assert result.total == 6586
