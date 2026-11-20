"""Tests for orders report handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_report, load


@pytest.fixture
def report():
    return make_report()


def test_load_report_single_0_runs():
    load(make_report())


def test_load_report_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    load(repo, 204)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(17, 34), (1, 2), (38, 76)])
def test_load_report_empty_2(value, expected):
    assert load(value) == expected


def test_load_report_edge_3(report):
    report.label = "refund-915"

    load(report)

    assert report.state == "open"


def test_load_report_empty_4():
    report = make_report(amount=64, count=37)

    result = load(report)

    assert result.total == 2368
