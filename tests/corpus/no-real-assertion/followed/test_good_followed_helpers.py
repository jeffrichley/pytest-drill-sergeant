"""Near-misses: the assertion is in a helper the test reaches through an import, its
class, a base class or a parameter, modelled on pandas' `_check_plot_works`,
`super().test_sort_values_frame()` and `_check_roundtrip(s, tm.assert_series_equal)`,
networkx's `self.test = partial(_test_func, ...)`; and a call into a third-party
package, code the check can't see, which may assert, as home-assistant's
`help_test_unique_id` from `pytest_homeassistant` does. Analysed, never run."""

from functools import partial

import frame_checks
import helpers
import pandas._testing as tm
import pytest
from base_tests import BaseOrderTests
from helpers import check_round_trip, check_through_another, round_trip, same
from pytest_homeassistant.components.mqtt.common import help_test_unique_id
from support import check_shipped

from conftest import check_receipt

pytestmark = pytest.mark.unit


def test_an_imported_helper_that_asserts_is_an_assertion():
    check_round_trip(3, str, int)


def test_an_imported_helper_that_calls_one_that_asserts_is_an_assertion():
    check_through_another(3)


def test_a_helper_reached_through_its_module_is_an_assertion():
    helpers.check_round_trip(3, str, int)


def test_a_helper_a_package_re_exports_is_an_assertion():
    check_shipped({"shipped": True})


def test_a_conftest_helper_is_an_assertion(receipt):
    check_receipt(receipt)


def test_a_helper_handed_an_assert_function_asserts():
    round_trip(3, tm.assert_almost_equal)


def test_a_helper_handed_an_asserting_helper_by_keyword_asserts():
    round_trip(3, compare=same)


class TestOrders(BaseOrderTests):
    def test_an_inherited_helper_that_asserts_is_an_assertion(self):
        self.check_order({"id": 1})

    def test_order_has_an_id(self, order):
        super().test_order_has_an_id(order)


class TestRoundTrips:
    @classmethod
    def setup_class(cls):
        cls.check = staticmethod(partial(check_round_trip, encode=str, decode=int))

    @classmethod
    def _check_all(cls, values):
        for value in values:
            cls._check_one(value)

    @classmethod
    def _check_one(cls, value):
        assert int(str(value)) == value

    def test_a_partial_bound_in_setup_class_is_an_assertion(self):
        self.check(3)

    def test_a_classmethod_helper_through_cls_is_an_assertion(self):
        self._check_all([3])


class TestCommonNeighbours:
    @classmethod
    def setup_class(cls):
        def check(graph, expected):
            assert sorted(graph) == expected

        cls.check = staticmethod(check)

    def test_a_function_defined_in_setup_class_is_an_assertion(self):
        self.check({2, 1}, [1, 2])


async def test_a_helper_from_a_third_party_package_may_assert(hass):
    await help_test_unique_id(hass, "light")


def test_a_function_through_a_third_party_module_may_assert(frame):
    frame_checks.verify(frame)
