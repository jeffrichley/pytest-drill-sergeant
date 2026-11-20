"""Test helpers the tests beside them import, as pandas' `tests/plotting/common.py`
and home-assistant's `tests/components/mqtt/common.py` are. Analysed, never run."""


def check_round_trip(value, encode, decode):
    assert decode(encode(value)) == value


def check_through_another(value):
    check_round_trip(value, str, int)


def round_trip(value, compare):
    compare(int(str(value)), value)


def build_order():
    return {"id": 1}


def same(left, right):
    assert left == right


def loosely_same(left, right):
    return str(left) == str(right)


class Checker:
    def verify(self, value):
        assert value == 1


def make_checker():
    return Checker()
