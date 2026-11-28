"""A conftest that gives the tests below it their own `mocker`. Analysed, never
run."""

import pytest
from shop import FakePatcher


@pytest.fixture(name="mocker")
def fake_mocker():
    return FakePatcher()
