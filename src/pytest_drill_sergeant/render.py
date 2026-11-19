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


def render(
    findings: list[Finding], *, voice: bool = True, max_findings: int = 0
) -> str:
    """Render findings as the report.

    The report is a banner, the findings grouped by file and findings by line, each
    with one voice line and plain Found/Why/Fix, and a closing tally by level with
    a flourish. With `max_findings`, only the first that many findings are shown, then a
    line counting the rest; the banner and tally still count every finding. With
    the voice off there is no banner, voice line or flourish; the
    Found/Why/Fix lines are unchanged.

    Args:
        findings: The findings to report, in the engine's order (by file, line and
            code), which keeps each file's findings together.
        voice: Whether to deliver the report in the voice.
        max_findings: The most findings to show; 0 shows them all.

    Returns:
        The report, ending in a newline.
    """
    if not findings:
        return (
            "DRILL SERGEANT INSPECTION: no findings. As you were!\n"
            if voice
            else "No findings.\n"
        )
    files = len({f.file for f in findings})
    out = []
    if voice:
        out += [
            f"DRILL SERGEANT INSPECTION: {_plural(len(findings), 'finding')} in "
            f"{_plural(files, 'file')}. FALL IN!",
            "",
        ]
    shown = findings[:max_findings] if max_findings else findings
    for file, group in groupby(shown, key=lambda f: f.file.as_posix()):
        out += [file]
        for f in group:
            out.append(f"  {file}:{f.line}: {f.code} {f.name} [{f.level}] in {f.test}")
            if voice:
                out.append(f'    "{_voice_line(f)}"')
            out += [
                f"    Found: {f.found}",
                f"    Why: {f.why}",
                f"    Fix: {f.fix}",
            ]
        out.append("")
    if len(shown) < len(findings):
        out += [
            f"…and {len(findings) - len(shown)} more, run `drill-sergeant check` "
            "for all",
            "",
        ]
    levels = Counter(f.level for f in findings)
    tally = (
        f"{_plural(len(findings), 'finding')}: {levels[Level.FAIL]} fail, "
        f"{levels[Level.WARN]} warn."
    )
    out.append(f"{tally} Fix them, recruit. DISMISSED!" if voice else tally)
    return "\n".join(out) + "\n"
