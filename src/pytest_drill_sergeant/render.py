"""The renderer: findings in, the drill sergeant's report out, as plain text."""

import hashlib
from collections import Counter
from itertools import groupby

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.findings import Finding, Level

_VOICE = {check.code: check.voice for check in CHECKS}


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _voice_line(finding: Finding) -> str:
    """The check's voice line for this finding.

    It's picked by a stable hash of (check, file, test), so the same finding always
    gets the same line.
    """
    lines = _VOICE[finding.code]
    key = f"{finding.code}|{finding.file.as_posix()}|{finding.test}".encode()
    return lines[int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % len(lines)]


def render(findings: list[Finding]) -> str:
    """Render findings as the report.

    The report is a banner, the findings grouped by file and findings by line, each
    with one voice line and plain Found/Why/Fix, and a closing tally by level.

    Args:
        findings: The findings to report, in the engine's order (by file, line and
            code), which keeps each file's findings together.

    Returns:
        The report, ending in a newline.
    """
    if not findings:
        return "DRILL SERGEANT INSPECTION: no findings. As you were!\n"
    files = len({f.file for f in findings})
    out = [
        f"DRILL SERGEANT INSPECTION: {_plural(len(findings), 'finding')} in "
        f"{_plural(files, 'file')}. FALL IN!",
    ]
    for file, group in groupby(findings, key=lambda f: f.file.as_posix()):
        out += ["", file]
        for f in group:
            out += [
                f"  {file}:{f.line}: {f.code} {f.name} [{f.level}] in {f.test}",
                f'    "{_voice_line(f)}"',
                f"    Found: {f.found}",
                f"    Why: {f.why}",
                f"    Fix: {f.fix}",
            ]
    levels = Counter(f.level for f in findings)
    out += [
        "",
        f"{_plural(len(findings), 'finding')}: {levels[Level.FAIL]} fail, "
        f"{levels[Level.WARN]} warn. Fix them, recruit. DISMISSED!",
    ]
    return "\n".join(out) + "\n"
