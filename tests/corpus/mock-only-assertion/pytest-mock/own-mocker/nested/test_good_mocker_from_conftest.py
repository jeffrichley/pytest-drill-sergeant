"""Near-misses: the project declares pytest-mock, but a conftest.py above this file
defines its own `mocker` fixture, which the tests get instead. Analysed, never
run."""

import pytest
from shop import defrost

pytestmark = pytest.mark.unit


def test_defrost_flag(mocker):
    thaw = mocker.patch("shop.thaw")
    defrost()
    assert thaw.called
