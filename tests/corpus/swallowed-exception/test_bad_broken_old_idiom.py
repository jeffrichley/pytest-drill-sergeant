"""The old way to write `pytest.raises`, broken: the handler also catches the
failure meant for when nothing is raised, or turns every error into a skip.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def parse(text):
    return int(text)


def test_handler_catches_the_assert_false():
    try:
        parse("x")
        assert False, "parse accepted garbage"
    except Exception:  # expect: DS702
        pass


def test_bare_handler_catches_pytest_fail():
    try:
        parse("x")
        pytest.fail("parse accepted garbage")
    # The bare `except` is the case under test.
    except:  # noqa: E722  # expect: DS702
        pass


def test_base_exception_handler_catches_pytest_fail():
    try:
        parse("x")
        pytest.fail("parse accepted garbage")
    except BaseException:  # expect: DS702
        pass


def test_handler_catches_the_raise():  # expect: DS101
    try:
        parse("x")
        raise RuntimeError("parse accepted garbage")
    except RuntimeError:  # expect: DS702
        pass


def test_skip_is_not_a_failure():  # expect: DS101
    try:
        parse("x")
        pytest.skip("parse accepted garbage")
    except ValueError:  # expect: DS702
        pass


def test_every_error_becomes_a_skip():
    try:
        value = parse("x")
    except Exception:  # expect: DS702
        pytest.skip("parse broke")
    assert value == 1
