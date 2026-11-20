"""Complete waivers on the flagged line silence that check's finding there."""

import pytest
from settings import read, read_flag

pytestmark = pytest.mark.unit


def test_reads_a_value():
    value = read()
    assert value is not None  # drill: waive DS201 -- read() may return anything


def test_reads_a_flag():
    flag = read_flag()
    assert flag  # drill:waive DS201--a truthy flag is the whole contract
