"""A `mocker` of the test's own that isn't a fixture it gets: a fixture in another
class, or a plain function. pytest-mock is declared, so the parameter is its
fixture. Analysed, never run."""

import pytest
from shop import FakePatcher, compact, rotate

pytestmark = pytest.mark.unit


def class_mocker():
    return FakePatcher()


class TestOwnPatcher:
    @pytest.fixture
    def mocker(self):
        return FakePatcher()


class TestRotate:
    def test_rotate_flag(self, mocker):  # expect: DS301
        roll = mocker.patch("shop.roll", autospec=True)
        rotate()
        assert roll.called


def test_compact_flag(class_mocker):  # expect: DS301
    squeeze = class_mocker.patch("shop.squeeze", autospec=True)
    compact()
    assert squeeze.called
