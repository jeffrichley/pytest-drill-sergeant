"""Tests for orders report handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_report, load


@pytest.fixture
def report():
    return make_report()


def test_load_report_many_0():
    report = make_report(amount=27, count=74)

    result = load(report)

    assert result.total == 1998


def test_load_report_empty_1_rejects_bad_input():
    with pytest.raises(ValueError, match="report"):
        load(None)


def test_load_report_basic_2():
    report = make_report(amount=75, count=10)

    result = load(report)

    assert result.total == 750


def test_load_report_large_3(report):
    report.label = "batch-85"

    load(report)

    assert report.state == "held"


def test_load_report_large_4():
    report = make_report(amount=29, count=22)

    result = load(report)

    assert result.total == 638


def test_load_report_basic_5_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    load(repo, 65)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
