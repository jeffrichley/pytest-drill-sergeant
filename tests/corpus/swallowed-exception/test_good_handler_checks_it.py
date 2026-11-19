"""Near-misses: handlers that assert on the exception, raise it again or end the
test on purpose. Analysed, never run."""

import pytest


def load(path):
    raise FileNotFoundError(path)


def test_handler_asserts_on_the_exception():
    try:
        load("app.toml")
    except FileNotFoundError as error:
        assert error.filename == "app.toml"


def test_handler_reraises():
    try:
        config = load("app.toml")
    except FileNotFoundError:
        print("cleanup")
        raise
    assert config == {}


def test_handler_raises_a_clearer_error():
    try:
        load("app.toml")
    except FileNotFoundError as error:
        raise AssertionError("config missing") from error


def test_handler_fails_the_test():
    try:
        load("app.toml")
    except OSError as error:
        pytest.fail(f"load raised {error}")


def test_handler_skips_when_a_dependency_is_missing():
    try:
        import tomllib
    except ImportError:
        pytest.skip("needs tomllib")
    assert tomllib.loads("a = 1") == {"a": 1}


def test_handler_marks_a_known_failure():
    try:
        load("app.toml")
    except FileNotFoundError:
        pytest.xfail("loader not written yet")
    assert load("app.toml") == {}


def test_handler_fails_through_the_bare_name():
    from pytest import fail

    try:
        load("app.toml")
    except OSError as error:
        fail(f"load raised {error}")
