"""Near-misses: functions with no assertion that pytest never collects as tests.
Analysed, never run."""

import pytest


def make_user():
    return {"name": "Ada"}


@pytest.fixture
def test_data():
    return make_user()


@pytest.fixture(scope="module")
def test_settings():
    return {}


class Helper:
    def test_like_but_not_collected(self):
        make_user()


class TestUser:
    def build(self):
        return make_user()

    def test_name(self, test_data):
        assert test_data["name"] == "Ada"
