"""The engine seam: what a call is, read from its definition in production code,
which the corpus has none of."""

import pytest

from pytest_drill_sergeant.engine import Config, analyze, inspect
from pytest_drill_sergeant.findings import Level

pytestmark = pytest.mark.unit

# DS201 and DS203 are off by default until they are proven.
ASSERTION_KINDS_ON = {"DS201": Level.FAIL, "DS203": Level.FAIL}
TRUTHINESS = "    ok = call(order)\n    assert ok\n"
SAME_CALL_TWICE = "    assert call(order) == call(order)\n"
PREDICATE = "def call(order) -> bool:\n    return order.flags\n"
VALUE = "def call(order):\n    return order.flags\n"


@pytest.mark.parametrize(
    ("body", "shop", "codes"),
    [
        (TRUTHINESS, PREDICATE, []),
        (TRUTHINESS, "def call(order):\n    return order.paid is True\n", []),
        (TRUTHINESS, VALUE, ["DS201"]),
        (SAME_CALL_TWICE, VALUE, ["DS203"]),
        (SAME_CALL_TWICE, "class call:\n    pass\n", []),
    ],
    ids=[
        "predicate-annotated-bool",
        "predicate-returning-a-comparison",
        "function-returning-a-value",
        "function-on-both-sides",
        "class-on-both-sides",
    ],
)
def test_assertion_checks_read_what_a_production_call_is_from_its_definition(
    production_caller, tmp_path, body, shop, codes
):
    """A call into production code is followed to its definition there: a predicate
    is exact, a function on both sides of `==` is a mirror, a class a constructor."""
    path = production_caller(body, shop)

    findings = analyze([path], Config(root=tmp_path, levels=ASSERTION_KINDS_ON))

    assert [f.code for f in findings] == codes


def test_editing_only_a_followed_production_definition_analyses_the_test_again(
    production_caller, tmp_path, cache_dir
):
    path = production_caller(TRUTHINESS, PREDICATE)
    config = Config(root=tmp_path, levels=ASSERTION_KINDS_ON)
    inspect([path], config, cache_dir=cache_dir)
    (tmp_path / "src" / "shop.py").write_text(VALUE)

    findings = inspect([path], config, cache_dir=cache_dir).findings

    assert [f.code for f in findings] == ["DS201"]
