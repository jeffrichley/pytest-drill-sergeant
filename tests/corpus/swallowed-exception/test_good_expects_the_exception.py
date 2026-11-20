"""Near-misses: the old way to write `pytest.raises`, where the `try` fails the
test when nothing is raised and the handler is the expected path. Analysed, never
run."""

import pytest


def parse(text):
    return int(text)


def test_body_ends_in_pytest_fail():
    try:
        parse("x")
        pytest.fail("parse accepted garbage")
    except ValueError:
        pass


def test_else_fails():
    try:
        parse("x")
    except ValueError:
        pass
    else:
        pytest.fail("parse accepted garbage")


def test_assert_false_after_a_returning_handler():
    try:
        parse("x")
    except ValueError:
        return
    assert False, "parse accepted garbage"


def test_body_ends_in_a_raise():
    try:
        parse("x")
        raise AssertionError("parse accepted garbage")
    except ValueError:
        pass


def test_specific_handler_cannot_catch_the_assert_false():
    try:
        parse("x")
        assert False, "parse accepted garbage"
    except ValueError:
        pass


def test_exception_handler_cannot_catch_pytest_fail():
    try:
        parse("x")
        pytest.fail("parse accepted garbage")
    except Exception:
        pass
