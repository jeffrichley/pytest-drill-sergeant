"""Near-misses: the project declares pytest-mock, but this module defines its own
`mocker` fixture, which the tests get instead. Analysed, never run."""

import pytest
from shop import FakePatcher, banner, prune

pytestmark = pytest.mark.unit


@pytest.fixture
def mocker():
    return FakePatcher()


def test_prune_flag(mocker):
    prune_all = mocker.patch("shop.prune_all")
    prune(["old"])
    assert prune_all.called


def test_banner_from_own_patcher(mocker):
    mocker.patch("shop.season", return_value="spring")
    assert banner() == "spring"
