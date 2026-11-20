"""Calls followed into the test tree that still check nothing, and calls that are
never followed: into production code, through a helper object some call returned
(home-assistant's `helper = setup_test_component(); helper.assert_values()`
shape, with no `assert*` name to go on), or into a module that isn't there. A
call into the project's own code, the standard library or pytest is code the
check sees, so it may not assert. Analysed, never run."""

import json

import pytest
from base_tests import BaseOrderTests
from helpers import build_order, loosely_same, make_checker, round_trip
from source.orders import ship, validate

pytestmark = pytest.mark.unit


def test_an_imported_helper_that_asserts_nothing_checks_nothing():  # expect: DS101
    build_order()


def test_an_assert_in_production_code_is_no_check_the_test_makes():  # expect: DS101
    validate({"id": 1})


def test_a_method_of_a_returned_helper_object_is_not_followed():  # expect: DS101
    checker = make_checker()
    checker.verify(1)


def test_a_helper_handed_a_function_that_asserts_nothing_checks_nothing():  # expect: DS101
    round_trip(3, loosely_same)


def test_a_helper_from_a_missing_module_is_not_followed():  # expect: DS101
    from .missing_helpers import check

    check(3)


def test_a_test_that_only_proves_nothing_raised_checks_nothing():  # expect: DS101
    build_order()
    round_trip(3, print)


class TestOrders(BaseOrderTests):
    def test_an_inherited_helper_checks_nothing(self):  # expect: DS101
        self.build()

    def test_order_builds(self):  # expect: DS101
        super().test_order_builds()


class TestCommonNeighbours:
    @classmethod
    def setup_class(cls):
        def render(graph):
            return sorted(graph)

        cls.render = staticmethod(render)

    def test_a_set_up_function_checks_nothing(self):  # expect: DS101
        self.render({2, 1})


def test_a_call_into_the_projects_own_code_checks_nothing():  # expect: DS101
    ship({"id": 1})


def test_a_call_into_the_standard_library_checks_nothing():  # expect: DS101
    json.dumps({"id": 1})


def test_a_call_into_pytest_checks_nothing():  # expect: DS101
    pytest.importorskip("numpy")
