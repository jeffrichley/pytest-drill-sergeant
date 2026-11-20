"""A test helper in a package below the tests. Analysed, never run."""


def check_shipped(order):
    assert order["shipped"] is True
