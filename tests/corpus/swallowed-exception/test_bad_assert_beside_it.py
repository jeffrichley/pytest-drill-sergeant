"""Swallowed exceptions with real assertions elsewhere in the test, so only the
handler gives them away. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def load(path):
    raise FileNotFoundError(path)


def test_load_asserts_only_on_success():
    try:
        config = load("app.toml")
    except FileNotFoundError:  # expect: DS702
        pass
    else:
        assert config == {"debug": False}


def test_load_one_handler_checks_the_other_drops():
    try:
        load("app.toml")
    except FileNotFoundError as error:
        assert error.filename == "app.toml"
    except PermissionError:  # expect: DS702
        pass


def test_load_trivial_assert_in_the_handler():
    try:
        load("app.toml")
    except OSError:  # expect: DS702
        assert True
    assert load("other.toml") == {}


def test_load_falls_back_to_a_default():
    try:
        config = load("app.toml")
    except (FileNotFoundError, PermissionError):  # expect: DS702
        config = {}
    assert config == {}
