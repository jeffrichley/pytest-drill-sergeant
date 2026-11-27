"""The engine seam: what a finding's text says, beyond its code and line."""

import pytest

from pytest_drill_sergeant.engine import Config, analyze
from pytest_drill_sergeant.findings import Level

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("values", "can_run_zero_times"),
    [
        ('("a", "b")', False),
        ('["a"]', False),
        ('{"a", *more}', False),
        ("()", True),
        ("(*more,)", True),
        ("WORDS", True),
        ("words()", True),
    ],
)
def test_loop_finding_says_zero_times_only_when_the_loop_can_run_zero_times(
    write_test_file, values, can_run_zero_times
):
    path = write_test_file(
        f"WORDS = ('a',)\n\ndef test_text(text, more, words):\n"
        f"    for word in {values}:\n        assert word not in text\n"
    )

    [finding] = analyze([path], Config(levels={"DS107": Level.FAIL}))

    assert finding.code == "DS107"
    assert ("zero times" in finding.found) is can_run_zero_times


@pytest.mark.parametrize(
    ("loop", "suggested"),
    [
        ('    for word in ("a", "b"):\n        assert word not in text\n', True),
        ("    for word in WORDS:\n        assert word not in text\n", True),
        ("    for word in (first, last):\n        assert word not in text\n", False),
        (
            "    seen = 0\n    for word in ('a', 'b'):\n        seen += len(word)\n"
            "        assert seen < len(text)\n",
            False,
        ),
        ('    for _ in ("a", "b"):\n        assert text\n', False),
    ],
    ids=["literals", "module-literal", "local-names", "carried-state", "unread-target"],
)
def test_loop_fix_suggests_parametrize_only_over_written_out_values_read_fresh(
    write_test_file, loop, suggested
):
    """Only literal values (or a module-level literal), read by a loop that carries
    nothing from one pass to the next, make a `parametrize`."""
    path = write_test_file(
        "WORDS = ('a',)\n\ndef test_text(text, first, last):\n" + loop
    )

    [finding] = analyze([path], Config(levels={"DS107": Level.FAIL}))

    assert ("parametrize" in finding.fix) is suggested


@pytest.mark.parametrize(
    ("source", "where"),
    [
        (
            "import pytest\n\nclass TestHtml:\n    def test_encode(self, ok):\n"
            "        if not ok:\n            pytest.skip()\n",
            "TestHtml::test_encode",
        ),
        (
            "import pytest\n\nclass TestHtml:\n    class TestUtf8:\n"
            "        def test_encode(self, ok):\n"
            "            if not ok:\n                pytest.skip()\n",
            "TestHtml::TestUtf8::test_encode",
        ),
        (
            "import pytest\n\ndef test_encode(ok):\n    def check():\n"
            "        if not ok:\n            pytest.skip()\n    check()\n",
            "test_encode",
        ),
    ],
    ids=["method", "nested-class", "function-in-a-test"],
)
def test_skip_call_finding_names_the_test_it_is_in(write_test_file, source, where):
    path = write_test_file(source)

    findings = analyze([path], Config(levels={"DS401": Level.FAIL}))

    assert [(f.code, f.test) for f in findings if f.code == "DS401"] == [
        ("DS401", where)
    ]


@pytest.mark.parametrize(
    ("body", "waiver_offered"),
    [("    ship(order)\n", True), ("    receipt = ship(order)\n", False)],
    ids=["result-discarded", "result-kept"],
)
def test_no_assertion_fix_offers_a_waiver_only_when_the_last_call_is_discarded(
    write_test_file, body, waiver_offered
):
    """A test that only proves a call doesn't raise gets no exemption: its fix says
    to waive it with that reason."""
    path = write_test_file("def test_ship(order):\n" + body)

    [finding] = analyze([path], Config(levels={"DS101": Level.FAIL}))

    assert ("# drill: waive DS101" in finding.fix) is waiver_offered
