"""Tests for shipping report handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_report, split

pytestmark = pytest.mark.unit


@pytest.fixture
def report():
    return make_report()


def test_split_report_basic_0(report):
    report.label = "event-984"

    split(report)

    assert report.state == "done"


def test_split_report_edge_1(report):
    report.label = "refund-257"

    split(report)

    assert report.state == "held"


def test_split_report_large_2():
    report = make_report(amount=90, count=88)

    result = split(report)

    assert result.total == 7920


def test_split_report_empty_3_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        split(None)


def test_split_report_empty_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    split(repo, 273)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_report_single_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    split(repo, 286)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_split_report_empty_6_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        split(None)
