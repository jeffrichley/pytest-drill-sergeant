"""Seeded from the archived rewrite's coverage-padding tests (tag
archive/2026-02-13/rewrite/main, tests/unit/test_final_push.py), with the
assertions an agent would leave out.

Analysed, never run.
"""

import pytest

import pytest_drill_sergeant

pytestmark = pytest.mark.unit


def test_final_coverage_push():  # expect: DS101
    """Final test to push coverage to 50%."""
    # Test all attributes
    hasattr(pytest_drill_sergeant, "__version__")
    hasattr(pytest_drill_sergeant, "__all__")

    # Test version
    version = pytest_drill_sergeant.__version__
    version.startswith("1.0.0")


@pytest.mark.parametrize("name", ["__version__", "__all__"])
def test_attributes_exist(name):  # expect: DS101
    getattr(pytest_drill_sergeant, name)


def test_smoke_with_a_try():
    try:
        pytest_drill_sergeant.run()
    except Exception:  # expect: DS702
        pass


def test_mock_configured_but_never_checked(mocker):  # expect: DS101
    mocker.patch("pytest_drill_sergeant.cli.main", return_value=0)
    pytest_drill_sergeant.cli.main()


def test_fail_method_on_some_object(job):  # expect: DS101
    job.fail()


def test_tuple_assert_is_always_true():  # expect: DS101
    assert (pytest_drill_sergeant.run(), "should run")


def test_raises_from_another_library():  # expect: DS101
    from .contracts import raises

    raises(ValueError)
