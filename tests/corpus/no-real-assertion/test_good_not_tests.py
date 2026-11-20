"""Near-misses: functions with no assertion that pytest never collects as tests.
Analysed, never run."""

import pytest
from pytest import fixture

pytestmark = pytest.mark.unit


def make_user():
    return {"name": "Ada"}


@pytest.fixture
def test_data():
    return make_user()


@pytest.fixture(scope="module")
def test_settings():
    return {}


@fixture
def test_imported_fixture():
    return make_user()


class Helper:
    def test_like_but_not_collected(self):
        make_user()


class TestUser:
    def build(self):
        return make_user()

    def test_name(self, test_data):
        assert test_data["name"] == "Ada"


class TestWithInit:
    def __init__(self):
        self.user = make_user()

    def test_not_collected(self):
        make_user()


class TestOptedOut:
    __test__ = False

    def test_not_collected(self):
        make_user()
