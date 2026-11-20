"""Tests for auth report handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_report, load


@pytest.fixture
def report():
    return make_report()


def test_load_report_single_0(report):
    report.label = "address-260"

    load(report)

    assert report.state == "held"


def test_load_report_large_1(report):
    report.label = "session-424"

    load(report)

    assert report.state == "open"


def test_load_report_many_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    load(repo, 189)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_report_empty_3():
    report = make_report(amount=62, count=62)

    result = load(report)

    assert result.total == 3844
