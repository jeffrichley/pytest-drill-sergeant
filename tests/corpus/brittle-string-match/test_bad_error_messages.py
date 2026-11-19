"""Exact error-message prose compared with `==`. Analysed, never run."""

import pytest
from app import InvalidEmail, ship, validate


def test_invalid_email_message():
    with pytest.raises(ValueError) as excinfo:
        validate("nope")
    assert (  # expect: DS601
        str(excinfo.value)
        == "Invalid email address: 'nope' does not contain an @ symbol."
    )


def test_message_attribute():
    with pytest.raises(InvalidEmail) as excinfo:
        validate("")
    assert (  # expect: DS601
        excinfo.value.message == "The email address must not be empty"
    )


def test_stripped_message_on_the_left():
    try:
        ship(order_id=7)
    except RuntimeError as err:
        assert "Order 7 could not be shipped" == str(err).strip()  # expect: DS601


def test_f_string_message(order_id):
    with pytest.raises(RuntimeError) as excinfo:
        ship(order_id=order_id)
    assert (  # expect: DS601
        str(excinfo.value) == f"Order {order_id} could not be shipped today"
    )
