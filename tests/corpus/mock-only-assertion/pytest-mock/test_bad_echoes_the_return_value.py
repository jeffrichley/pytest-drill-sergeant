"""Tests that assert only what a mock was told to return, so they test the mock.
Analysed, never run."""

import pytest
from shop import Clock, CustomerService, Repo, label

pytestmark = pytest.mark.unit


def test_get_customer(mocker):  # expect: DS301
    repo = mocker.Mock(spec=Repo)
    repo.find_one.return_value = {"id": 1, "name": "Ada"}
    result = CustomerService(repo).get(1)
    assert result == {"id": 1, "name": "Ada"}
    repo.find_one.assert_called_once_with(1)


def test_label_uses_today(mocker):  # expect: DS301
    mocker.patch("shop.today", autospec=True, return_value="2026-01-01")
    assert label() == "2026-01-01"


def test_find_returns_what_the_repo_gives(mocker):  # expect: DS301
    repo = mocker.create_autospec(Repo, instance=True)
    service = CustomerService(repo)
    assert service.find(1) is repo.get.return_value


def test_clock_value_passed_through(mocker):  # expect: DS301
    clock = mocker.Mock(spec=Clock)
    reading = clock.now
    assert CustomerService(clock).stamp() == reading.return_value
