"""Near-misses: constant assertions no-real-assertion owns, beside a real one,
and a test whose only assertion is `assert False` on a branch. Analysed, never
run."""

from shop import parse


def test_assert_true_beside_a_real_assertion():
    assert True
    assert parse("4") == 4


def test_tuple_beside_a_real_assertion():
    assert parse("4") == 4
    assert (parse("5"), "always true")  # noqa: F631


def test_assert_false_on_the_unreachable_branch():
    try:
        parse("x")
    except ValueError:
        return
    assert False, "parse accepted garbage"
