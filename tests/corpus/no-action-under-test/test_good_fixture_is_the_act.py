"""Near-misses: no call in the body, but a fixture, parameter or setup method brings
the value under test. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_default_timeout(settings):
    assert settings.timeout == 30


@pytest.mark.parametrize("code", [200, 201])
def test_success_codes(code):
    assert 200 <= code < 300


class TestFromSetup:
    def setup_method(self):
        self.user = make_user()

    def test_name_from_setup(self):
        assert self.user["name"] == "Ada"


def make_user():
    return {"name": "Ada"}
