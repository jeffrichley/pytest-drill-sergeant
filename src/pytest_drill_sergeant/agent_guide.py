"""The agent guide, generated from the check registry, and its install into a repo.

The guide teaches a coding agent every check before it writes tests. `explain` shares
its rendering of a check, so the two can't drift apart or from the registry.

Installing it is a command a person runs, never part of a run: it writes the guide as
an Agent Skill and adds a short version-marked block pointing at it to the repo's
AGENTS.md or CLAUDE.md, replacing only that block on a rerun.
"""

import re
from importlib.metadata import version
from pathlib import Path

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


class InstallError(ValueError):
    """The guide can't be installed; the message names why, in one line."""


SKILL_NAME = "drill-sergeant"
# Plain YAML: no `: ` or ` #` in it.
SKILL_DESCRIPTION = (
    "The drill-sergeant agent guide, teaching every check this repo's tests must "
    "pass. Use before writing or changing a test, or when fixing a drill-sergeant "
    "finding."
)

# Where the agents that read AGENTS.md, or CLAUDE.md, look for skills.
SKILL_DIRS = {"AGENTS.md": ".agents/skills", "CLAUDE.md": ".claude/skills"}

# The block's markers: its end, and its start as any version of drill-sergeant
# wrote it, to find and replace.
_END = "<!-- /drill-sergeant agent guide -->"
_START_OF_ANY_VERSION = re.compile(r"<!-- drill-sergeant agent guide v\S+ -->")


def _start_of_this_version() -> str:
    """The block's start marker as this version of drill-sergeant writes it."""
    return f"<!-- drill-sergeant agent guide v{version('pytest-drill-sergeant')} -->"


def skill() -> str:
    """The Agent Skill that holds the full guide."""
    return (
        f"---\nname: {SKILL_NAME}\ndescription: {SKILL_DESCRIPTION}\n---\n\n{guide()}\n"
    )


def block(skill_path: str) -> str:
    """The version-marked block for AGENTS.md or CLAUDE.md that points at the skill."""
    return (
        f"{_start_of_this_version()}\n"
        "## Tests: drill-sergeant\n\n"
        "This repo checks its tests with drill-sergeant: every pytest run fails on "
        "findings about how the tests are written. Before you write or change a test, "
        f"read the agent guide in the `{SKILL_NAME}` skill (`{skill_path}`) or run "
        "`drill-sergeant agent-guide`; `drill-sergeant explain DS###` teaches one "
        "check.\n\n"
        f"{WAIVER_RULE}\n"
        f"{_END}"
    )


def _with_block(text: str, new_block: str) -> str | None:
    """AGENTS.md or CLAUDE.md text with the block refreshed in place, or appended.

    `None` when the text has the block's start marker but no end marker after it.
    """
    start = _START_OF_ANY_VERSION.search(text)
    if start is None:
        return f"{text.rstrip()}\n\n{new_block}\n" if text.strip() else f"{new_block}\n"
    end = text.find(_END, start.end())
    if end == -1:
        return None
    return text[: start.start()] + new_block + text[end + len(_END) :]


def install(root: Path) -> list[Path]:
    """Install the guide into the repo at root; return the files written.

    The block goes in AGENTS.md if it exists, else CLAUDE.md if that does, else a new
    AGENTS.md; the skill goes where that file's agents look. A file whose content
    would not change is left as it is.
    """
    name = next(
        (n for n in ("AGENTS.md", "CLAUDE.md") if (root / n).is_file()), "AGENTS.md"
    )
    skill_path = f"{SKILL_DIRS[name]}/{SKILL_NAME}/SKILL.md"
    block_file = root / name
    existing = block_file.read_text() if block_file.is_file() else ""
    refreshed = _with_block(existing, block(skill_path))
    if refreshed is None:
        raise InstallError(
            f"{name} has the agent guide's start marker but no `{_END}` after it"
        )
    contents = {block_file: refreshed, root / skill_path: skill()}
    written = []
    for path, content in contents.items():
        if path.is_file() and path.read_text() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written.append(path)
    return written
