"""Tests for orders report handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_report, render


@pytest.fixture
def report():
    return make_report()


def test_render_report_many_0(report):
    report.label = "cart-294"

    render(report)

    assert report.state == "done"


def test_render_report_large_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    render(repo, 39)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_report_many_2():
    report = make_report(amount=12, count=20)

    result = render(report)

    assert result.total == 240


def test_render_report_empty_3_runs():
    render(make_report())


def test_render_report_many_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_report()

    render(repo, 184)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
