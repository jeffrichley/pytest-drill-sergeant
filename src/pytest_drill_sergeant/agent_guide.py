"""The agent guide, generated from the check registry, and its install into a repo.

The guide teaches a coding agent every check before it writes tests. `explain` shares
its rendering of a check, so the two can't drift apart or from the registry.
"""

from pytest_drill_sergeant.checks import CHECKS, Check

# The rule every form of the guide states, word for word.
WAIVER_RULE = (
    "You may ask a human to waive a finding you believe is a false positive, but you "
    "add a waiver or change drill-sergeant's config only after an explicit yes from a "
    "human for that specific finding."
)

EXPLAIN_POINTER = "`drill-sergeant explain DS###` shows a check's bad and fixed test."


def lesson(check: Check) -> str:
    """One check taught in full: its rationale, then a test it flags and the fix."""
    return (
        f"{check.code} {check.name} [{check.default_level}]\n\n"
        f"Why: {check.why}\n\n"
        f"{check.explain}\n\n"
        f"Bad:\n\n{check.bad_example}\n"
        f"Good:\n\n{check.good_example}"
    )


def summary() -> str:
    """Every check in a line: its code, name and default level, and why it matters."""
    return "\n".join(
        f"{check.code} {check.name} [{check.default_level}]: {check.why}"
        for check in CHECKS
    )


def guide() -> str:
    """The full agent guide.

    What drill-sergeant does, the waiver rule, then every check in a line and in full.
    """
    lessons = "\n\n".join(lesson(check) for check in CHECKS)
    return (
        "# drill-sergeant agent guide\n\n"
        "This repo's tests are checked by drill-sergeant. Every pytest run analyses "
        "the test files it collects and fails on findings about how the tests are "
        "written, even when every test passes; `drill-sergeant check <paths>` reports "
        "the same findings without running the tests. Learn the checks below before "
        "you write or change a test, and write tests that pass them. Each finding "
        f"names its check's `DS###` code; {EXPLAIN_POINTER}\n\n"
        "## Waivers\n\n"
        f"{WAIVER_RULE} A waiver is a `# drill: waive DS### -- <reason>` comment on "
        "the test's `def` line or on the finding's line, giving the reason the human "
        "agreed to.\n\n"
        "## The checks\n\n"
        f"{summary()}\n\n"
        "## Each check in full\n\n"
        f"{lessons}"
    )
