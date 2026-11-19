"""Near-misses: text compared with `==` against short literals, which pin a value,
not prose. Analysed, never run."""

from app import Money, Point, User, cli


def test_number_renders():
    assert str(3) == "3"


def test_money_renders():
    assert str(Money(300)) == "$3.00"


def test_point_repr():
    assert repr(Point(1, 2)) == "Point(x=1, y=2)"


def test_quiet_run_prints_nothing(runner):
    assert runner.invoke(cli, ["--quiet"]).output == ""


def test_status_word(runner):
    assert runner.invoke(cli, ["ping"]).stdout == "pong\n"


def test_full_name():
    assert User(first="Ada", last="Lovelace").name == "Ada Lovelace"
