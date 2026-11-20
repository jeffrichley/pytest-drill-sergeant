"""The engine: test files and a config in, findings out, with no pytest in sight."""

import ast
from collections.abc import Iterable, Iterator, Mapping
from fnmatch import fnmatch
from pathlib import Path

from pytest_drill_sergeant.checks import CHECKS, Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.ast_tools import (
    FIXTURE_DECORATORS,
    imports_seen_by,
    module_imports,
    qualified,
)
from pytest_drill_sergeant.checks.base import FileSummary, FunctionNode, Thresholds
from pytest_drill_sergeant.checks.summary import summarize
from pytest_drill_sergeant.config import Config
from pytest_drill_sergeant.findings import Finding, Level

__all__ = ["Config", "analyze"]


def _is_fixture(node: FunctionNode, names: Mapping[str, str]) -> bool:
    """Whether a function is a pytest fixture, which pytest never collects as a test.

    Its decorator is `pytest.fixture` (or `pytest_asyncio.fixture`), called or not,
    through whatever name the imports give it.
    """
    return any(
        qualified(d.func if isinstance(d, ast.Call) else d, names) in FIXTURE_DECORATORS
        for d in node.decorator_list
    )


def _is_collected_class(node: ast.ClassDef) -> bool:
    """Whether pytest collects a class.

    It does when the class is named `Test*`, has no `__init__` and isn't opted out
    with `__test__ = False`.
    """
    if not node.name.startswith("Test"):
        return False
    for statement in node.body:
        if isinstance(statement, ast.FunctionDef) and statement.name == "__init__":
            return False
        if (
            isinstance(statement, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "__test__"
                for t in statement.targets
            )
            and isinstance(statement.value, ast.Constant)
            and not statement.value.value
        ):
            return False
    return True


def _tests_in(
    body: list[ast.stmt], names: Mapping[str, str], prefix: str = ""
) -> Iterator[TestFunction]:
    """The tests pytest's default rules collect.

    Those are `test*` functions that aren't fixtures, at module level or in the
    classes pytest collects, nested ones included.
    """
    for node in body:
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("test")
            and not _is_fixture(node, names)
        ):
            yield TestFunction(
                name=f"{prefix}{node.name}",
                node=node,
                imports=imports_seen_by(node, names),
            )
        elif isinstance(node, ast.ClassDef) and _is_collected_class(node):
            yield from _tests_in(node.body, names, f"{prefix}{node.name}::")


def _ignored_codes(path: Path, config: Config) -> frozenset[str]:
    """The code prefixes the config's per-file ignores turn off for a file.

    A glob matches the file's path relative to the config root, or, for a glob with
    no `/`, the file's name.
    """
    resolved = path.resolve()
    root = config.root.resolve()
    relative = (
        resolved.relative_to(root).as_posix()
        if resolved.is_relative_to(root)
        else path.as_posix()
    )
    ignored: set[str] = set()
    for glob, codes in config.per_file_ignores:
        if fnmatch(relative, glob) or ("/" not in glob and fnmatch(path.name, glob)):
            ignored |= codes
    return frozenset(ignored)


def _thresholds(config: Config) -> Thresholds:
    return Thresholds(
        max_file_lines=config.max_file_lines,
        max_test_lines=config.max_test_lines,
        max_mock_setup=config.max_mock_setup,
        duplicate_setup_min_statements=config.duplicate_setup_min_statements,
        duplicate_setup_min_tests=config.duplicate_setup_min_tests,
    )


def _level(check: Check, ignored: frozenset[str], config: Config) -> Level:
    """The level a check reports at in a file, `off` if it doesn't report there."""
    level = config.levels.get(check.code, check.default_level)
    if level is Level.OFF or any(check.code.startswith(c) for c in ignored):
        return Level.OFF
    return Level.WARN if config.mode is Level.WARN else level


def _finding(check: Check, path: Path, hit: Hit, level: Level) -> Finding:
    return Finding(
        code=check.code,
        name=check.name,
        file=path,
        line=hit.line,
        test=hit.test,
        level=level,
        found=hit.found,
        why=check.why,
        fix=hit.fix,
    )


def _analyze_file(path: Path, config: Config) -> tuple[list[Finding], FileSummary]:
    """Per-file analysis: one file's own findings, and its per-file summary."""
    module = ast.parse(path.read_bytes(), filename=str(path))
    tests = tuple(_tests_in(module.body, module_imports(module)))
    file = TestFile(
        path=path, module=module, tests=tests, thresholds=_thresholds(config)
    )
    ignored = _ignored_codes(path, config)
    findings = [
        _finding(check, path, hit, level)
        for check in CHECKS
        if (level := _level(check, ignored, config)) is not Level.OFF
        for hit in check.find(file)
    ]
    return findings, summarize(file)


def _compare_files(
    summaries: list[tuple[Path, FileSummary]], config: Config
) -> list[Finding]:
    """Cross-file analysis: the findings comparing every file's summary turns up.

    A file a per-file ignore keeps a check off is left out of that check's
    comparison.
    """
    findings: list[Finding] = []
    ignored = {path: _ignored_codes(path, config) for path, _ in summaries}
    for check in CHECKS:
        seen = [
            (path, summary)
            for path, summary in summaries
            if _level(check, ignored[path], config) is not Level.OFF
        ]
        findings.extend(
            _finding(check, path, hit, _level(check, ignored[path], config))
            for path, hit in check.find_across(seen, _thresholds(config))
        )
    return findings


def analyze(paths: Iterable[Path], config: Config) -> list[Finding]:
    """Run every check over the test files and return the findings.

    Each file is analysed on its own, for its findings and its per-file summary;
    then the summaries, never the files, are compared across files.

    Args:
        paths: The test files to analyse.
        config: The resolved configuration.

    Returns:
        The findings, ordered by file, line and code. Checks configured `off`
        report none, nor do checks a per-file ignore names for a file, and none run
        in `off` mode; in `warn` mode every finding is reported as `warn`.
    """
    if config.mode is Level.OFF:
        return []
    findings: list[Finding] = []
    summaries: list[tuple[Path, FileSummary]] = []
    for path in sorted(paths, key=lambda p: p.as_posix()):
        file_findings, summary = _analyze_file(path, config)
        findings.extend(file_findings)
        summaries.append((path, summary))
    findings.extend(_compare_files(summaries, config))
    return sorted(findings, key=lambda f: (f.file.as_posix(), f.line, f.code))
