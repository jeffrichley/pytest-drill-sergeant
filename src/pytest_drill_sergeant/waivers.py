"""Inline waivers: reading them from a test file, and applying them to findings.

A waiver is a comment, `# drill: waive DS### -- <reason>`, on a test's `def` line
or on the line a finding is reported on. It waives the findings of the check it
names on that line, or anywhere in that test when it sits on the `def` line. Only
comments count: the same text in a string or docstring is not a waiver.

A comment that starts `# drill: waive` but gives no code, or no reason after `--`,
waives nothing; the malformed-waiver check (DS001) reports it instead.
"""

import io
import re
import tokenize
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.findings import Finding

# The malformed-waiver check's code: its own findings are never waived.
MALFORMED_WAIVER = "DS001"

_WAIVER = re.compile(r"#\s*drill:\s*waive\b(?P<rest>.*)", re.DOTALL)
_CODE = re.compile(r"DS\d{3}")


@dataclass(frozen=True)
class Waiver:
    """One `# drill: waive` comment, as written.

    Attributes:
        line: The line the comment is on.
        code: The check code it names, or "" when it names none.
        reason: The reason after `--`, or "" when it gives none.
    """

    line: int
    code: str
    reason: str

    @property
    def complete(self) -> bool:
        """Whether it names a code and gives a reason, so it can waive a finding."""
        return bool(self.code and self.reason)


@dataclass(frozen=True)
class WaivedFinding:
    """A finding a waiver silenced, and the reason the waiver gives.

    Attributes:
        finding: The finding, as the check reported it.
        reason: The waiver's reason.
    """

    finding: Finding
    reason: str


@dataclass(frozen=True)
class FileWaivers:
    """What applying waivers needs from one test file.

    Attributes:
        waivers: The file's `# drill: waive` comments, in line order.
        def_lines: Each test's `def` line, by the test's name.
    """

    waivers: tuple[Waiver, ...]
    def_lines: Mapping[str, int]


def _waiver(line: int, comment: str) -> Waiver | None:
    match = _WAIVER.match(comment)
    if match is None:
        return None
    head, _, reason = match["rest"].partition("--")
    words = head.split()
    code = words[0] if words and _CODE.fullmatch(words[0]) else ""
    return Waiver(line=line, code=code, reason=reason.strip())


def parse(source: bytes) -> tuple[Waiver, ...]:
    """The `# drill: waive` comments in a file's source, complete or not.

    Comments are read with `tokenize`, so text in a string is never a waiver.
    """
    tokens = tokenize.tokenize(io.BytesIO(source).readline)
    found = (
        _waiver(token.start[0], token.string)
        for token in tokens
        if token.type == tokenize.COMMENT
    )
    return tuple(w for w in found if w is not None)


def apply(
    findings: Iterable[Finding], files: Mapping[Path, FileWaivers]
) -> tuple[list[Finding], list[WaivedFinding]]:
    """Split findings into those that stand and those a waiver silences.

    A complete waiver silences a finding of the check it names when it sits on the
    finding's line or on its test's `def` line. A malformed-waiver finding is never
    silenced.

    Args:
        findings: The findings, in the engine's order.
        files: Each file's waivers and `def` lines, by the path its findings carry.

    Returns:
        The findings that stand, and the waived ones, both in the order given.
    """
    kept: list[Finding] = []
    waived: list[WaivedFinding] = []
    for finding in findings:
        reason = _reason_for(finding, files.get(finding.file))
        if reason is None or finding.code == MALFORMED_WAIVER:
            kept.append(finding)
        else:
            waived.append(WaivedFinding(finding=finding, reason=reason))
    return kept, waived


def _reason_for(finding: Finding, file: FileWaivers | None) -> str | None:
    """The reason of the waiver that silences a finding, if one does."""
    if file is None:
        return None
    lines = {finding.line, file.def_lines.get(finding.test)}
    return next(
        (
            w.reason
            for w in file.waivers
            if w.complete and w.code == finding.code and w.line in lines
        ),
        None,
    )
