"""Near-misses: a private exception or warning class that `pytest.raises` or
`pytest.warns` expects, known by its place in the call. Analysed, never run."""

import pytest
from app import Service

pytestmark = pytest.mark.unit


def test_raises_a_private_error():
    with pytest.raises(Service._Timeout):
        Service().run()


def test_raises_a_private_error_by_keyword():
    with pytest.raises(expected_exception=Service._Timeout):
        Service().run()


def test_warns_a_private_warning():
    with pytest.warns(Service._SlowWarning):
        Service().run()


def test_warns_a_private_warning_by_keyword():
    with pytest.warns(expected_warning=Service._SlowWarning):
        Service().run()
