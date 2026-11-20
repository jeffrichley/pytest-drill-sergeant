"""Assertions on private state read into a local variable first, traced through the
assignment. Seeded from stagehand's casting tests. Analysed, never run."""

import pytest
from app import Driver

pytestmark = pytest.mark.unit


def test_a_private_call_result_held_in_a_variable(tmp_path):
    opts = Driver(tmp_path)._options()
    assert opts.model is None  # expect: DS602
    assert opts.effort is None  # expect: DS602


def test_a_private_attribute_held_in_a_variable():
    driver = Driver("dee")
    driver.start()
    seats = driver._seats
    assert len(seats) == 1  # expect: DS602


def test_a_private_read_traced_through_two_variables():
    driver = Driver("dee")
    driver.start()
    opts = driver._options()
    model = opts.model
    assert model == "claude-sonnet-5"  # expect: DS602


def test_a_private_read_unpacked_into_names():
    driver = Driver("dee")
    model, effort = driver._casting()
    assert model is None and effort == "max"  # expect: DS602


def test_a_private_read_held_by_an_annotated_name():
    driver = Driver("dee")
    driver.start()
    opts: dict = driver._options()
    assert opts["model"] is None  # expect: DS602
