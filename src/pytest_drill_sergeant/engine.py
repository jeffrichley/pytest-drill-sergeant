"""The engine: test files, production code and a config in, findings out.

No pytest in sight.
"""

import ast
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from pytest_drill_sergeant.checks import (
    CHECKS,
    Check,
    Hit,
    SourceFile,
    TestFile,
    TestFunction,
)
from pytest_drill_sergeant.checks.ast_tools import (
    FIXTURE_DECORATORS,
    imports_seen_by,
    module_imports,
    qualified,
)
from pytest_drill_sergeant.checks.base import FunctionNode, Thresholds
from pytest_drill_sergeant.config import Config
from pytest_drill_sergeant.findings import Finding, Level
from pytest_drill_sergeant.waivers import (
    FileWaivers,
    WaivedFinding,
    apply,
    parse,
)

__all__ = ["Config", "Inspection", "analyze", "inspect"]


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


def _finding(check: Check, level: Level, path: Path, hit: Hit) -> Finding:
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


def _levelled_checks(path: Path, config: Config) -> Iterator[tuple[Check, Level]]:
    """The checks that report on a file, each with the level it reports at.

    Not the checks configured `off`, nor those a per-file ignore names for the
    file; in `warn` mode every level is `warn`.
    """
    ignored = _ignored_codes(path, config)
    for check in CHECKS:
        level = config.levels.get(check.code, check.default_level)
        if level is Level.OFF or any(check.code.startswith(c) for c in ignored):
            continue
        yield check, Level.WARN if config.mode is Level.WARN else level


@dataclass(frozen=True)
class Inspection:
    """What one run over the test files and production code found.

    Attributes:
        findings: The findings that stand, ordered by file, line and code.
        waived: The findings an inline waiver silenced, in the same order.
    """

    findings: list[Finding]
    waived: list[WaivedFinding]


def analyze(
    paths: Iterable[Path], config: Config, sources: Iterable[Path] = ()
) -> list[Finding]:
    """Run every check over the test files and production code; return what stands.

    The same as `inspect(paths, config, sources).findings`.
    """
    return inspect(paths, config, sources).findings


def inspect(
    paths: Iterable[Path], config: Config, sources: Iterable[Path] = ()
) -> Inspection:
    """Run every check over the test files and production code, then apply waivers.

    The waivers are the files' inline waivers.

    Args:
        paths: The test files to analyse.
        config: The resolved configuration.
        sources: The production files to analyse, read in full, by the checks
            that read production code (DS403) and no others. A waiver there
            silences a finding on its own line.

    Returns:
        The findings that stand and the waived ones, each ordered by file, line
        and code. Checks configured `off` report none, nor do checks a per-file
        ignore names for a file, and none run in `off` mode; in `warn` mode every
        finding is reported as `warn`. With inline waivers off, no finding is
        waived and malformed waivers (DS001) aren't reported.
    """
    thresholds = Thresholds(
        max_file_lines=config.max_file_lines,
        max_test_lines=config.max_test_lines,
        max_mock_setup=config.max_mock_setup,
    )
    findings: list[Finding] = []
    files: dict[Path, FileWaivers] = {}
    if config.mode is Level.OFF:
        return Inspection(findings=findings, waived=[])
    for path in paths:
        source = path.read_bytes()
        module = ast.parse(source, filename=str(path))
        tests = tuple(_tests_in(module.body, module_imports(module)))
        waivers = parse(source) if config.inline_waivers else ()
        files[path] = FileWaivers(
            waivers=waivers, def_lines={t.name: t.node.lineno for t in tests}
        )
        file = TestFile(
            path=path,
            module=module,
            tests=tests,
            waivers=waivers,
            thresholds=thresholds,
        )
        for check, level in _levelled_checks(path, config):
            findings.extend(
                _finding(check, level, path, hit) for hit in check.find(file)
            )
    for path in sources:
        source = path.read_bytes()
        production = SourceFile(path=path, module=ast.parse(source, filename=str(path)))
        files.setdefault(
            path,
            FileWaivers(
                waivers=parse(source) if config.inline_waivers else (), def_lines={}
            ),
        )
        for check, level in _levelled_checks(path, config):
            if check.find_in_source is not None:
                findings.extend(
                    _finding(check, level, path, hit)
                    for hit in check.find_in_source(production)
                )
    findings.sort(key=lambda f: (f.file.as_posix(), f.line, f.code))
    kept, waived = apply(findings, files)
    return Inspection(findings=kept, waived=waived)
