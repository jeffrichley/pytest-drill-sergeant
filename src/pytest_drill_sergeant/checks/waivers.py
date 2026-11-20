"""The drill-sergeant family (DS0xx): how drill-sergeant itself is used."""

from collections.abc import Iterator

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile
from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.waivers import MALFORMED_WAIVER as MALFORMED_WAIVER_CODE
from pytest_drill_sergeant.waivers import Waiver

# The name a finding outside every test is reported under.
_MODULE = "<module>"


def _missing(waiver: Waiver) -> str:
    if not waiver.code and not waiver.reason:
        return "no check code and no reason"
    return "no check code" if not waiver.code else "no reason after `--`"


def _test_at(file: TestFile, line: int) -> str:
    """The name of the test whose code holds a line, or `<module>` outside them."""
    return next(
        (
            t.name
            for t in file.tests
            if t.node.lineno <= line <= (t.node.end_lineno or t.node.lineno)
        ),
        _MODULE,
    )


def _find_malformed_waiver(file: TestFile) -> Iterator[Hit]:
    for waiver in file.waivers:
        if waiver.complete:
            continue
        test = _test_at(file, waiver.line)
        where = "Line" if test == _MODULE else f"In `{test}`, line"
        code = waiver.code or "DS###"
        yield Hit(
            line=waiver.line,
            test=test,
            found=(
                f"The waiver on line {waiver.line} gives {_missing(waiver)}, "
                "so it waives nothing."
            ),
            fix=(
                f"{where} {waiver.line}: write it as "
                f"`# drill: waive {code} -- <reason>` once a human has agreed to "
                "waive this finding, or remove it and fix the finding."
            ),
        )


MALFORMED_WAIVER = Check(
    code=MALFORMED_WAIVER_CODE,
    name="malformed-waiver",
    default_level=Level.FAIL,
    voice=(
        "A waiver without a code AND a reason is just a shrug in a comment, recruit!",
        "You want out of an inspection? Name the check and SAY WHY, maggot!",
        "Nobody silences my findings with a mumble! Code and reason, or fix it!",
    ),
    why=(
        "A waiver must name the check it silences and say why, so a reviewer can "
        "judge it; without both it waives nothing and hides what was meant."
    ),
    explain=(
        "Flags a `# drill: waive` comment that gives no check code or no reason. A "
        "waiver is written `# drill: waive DS### -- <reason>` on the test's `def` "
        "line or the line a finding is reported on, and silences only that check's "
        "findings there. Add both, after a human has agreed to waive that specific "
        "finding, or remove the comment and fix the finding. With "
        "`drill_sergeant_inline_waivers = false`, waivers are ignored and this check "
        "reports nothing."
    ),
    bad_example=("def test_cli_smoke():  # drill: waive\n    main(['--help'])\n"),
    good_example=(
        "def test_cli_smoke():  # drill: waive DS101 -- exit code checked by CI\n"
        "    main(['--help'])\n"
    ),
    find=_find_malformed_waiver,
)
