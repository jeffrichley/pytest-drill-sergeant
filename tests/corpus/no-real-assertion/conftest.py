"""A `conftest.py` above the tests that import from it: in the test tree wherever it
sits. Analysed, never run."""


def check_receipt(receipt):
    assert receipt.total == 3
