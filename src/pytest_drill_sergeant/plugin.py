"""The pytest plugin, registered through the `pytest11` entry point.

Installing the package turns it on; `-p no:drill_sergeant` or
`drill_sergeant_mode = off` turns it off. After collection it analyses the files that
contributed collected test functions, once, on the xdist controller only; the tests
then run as always. The findings section after the test results shows them, and a
run whose tests ran and passed exits 1 when any finding is at the `fail` level.
"""

from pathlib import Path

import pytest

from pytest_drill_sergeant.config import OPTIONS, Config, resolve
from pytest_drill_sergeant.engine import analyze
from pytest_drill_sergeant.findings import Finding, Level
from pytest_drill_sergeant.render import render

# The name the run's state is registered under with pytest's plugin manager.
_RUN = "drill_sergeant_run"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register every `drill_sergeant_*` ini option."""
    for option in OPTIONS:
        parser.addini(
            option.name, option.help, type=option.kind, default=option.default
        )


def _require_config(config: pytest.Config) -> Config:
    """The resolved drill-sergeant config.

    Raises:
        pytest.UsageError: When the config is wrong, naming what in one line.
    """
    try:
        raw = {option.name: config.getini(option.name) for option in OPTIONS}
        root = config.inipath.parent if config.inipath else config.rootpath
        return resolve(raw, root=root)
    # pytest's own parsing of an int or bool ini value raises these; `ConfigError`
    # is a `ValueError`.
    except (ValueError, TypeError) as error:
        raise pytest.UsageError(f"drill-sergeant: {error}") from None


def pytest_configure(config: pytest.Config) -> None:
    """Resolve the config and, unless the mode is `off`, start the run.

    An xdist worker only runs tests and tells the controller which files it collected
    them from; the controller analyses.
    """
    resolved = _require_config(config)
    if resolved.mode is Level.OFF:
        return
    if hasattr(config, "workerinput"):
        config.pluginmanager.register(_Worker(config), _RUN)
    else:
        config.pluginmanager.register(_Run(config, resolved), _RUN)


# The key under which an xdist worker sends the controller its collected files.
_FILES = "drill_sergeant_files"


def _collected_files(session: pytest.Session) -> set[Path]:
    """The files that contributed collected tests: test functions, not doctests."""
    return {item.path for item in session.items if isinstance(item, pytest.Function)}


class _Worker:
    """An xdist worker's part: report the files it collected tests from."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        """Hand the collected files to the controller."""
        output = self.config.workeroutput  # type: ignore[attr-defined]  # set by xdist
        output[_FILES] = sorted(str(path) for path in _collected_files(session))


class _Run:
    """One drill-sergeant run: the files analysed, the findings, the report."""

    def __init__(self, config: pytest.Config, resolved: Config) -> None:
        self.config = config
        self.resolved = resolved
        self.findings: list[Finding] | None = None

    def _analyze(self, paths: set[Path]) -> None:
        if self.findings is not None:
            return
        here = self.config.invocation_params.dir
        self.findings = analyze(
            sorted(p.relative_to(here) if p.is_relative_to(here) else p for p in paths),
            self.resolved,
        )

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        """Analyse the files that contributed collected tests."""
        self._analyze(_collected_files(session))

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node: object) -> None:
        """Analyse the files the first xdist worker to finish collected tests from.

        Every worker collects the same tests, so one worker's files are the run's.
        """
        files = getattr(node, "workeroutput", {}).get(_FILES)
        if files is not None:
            self._analyze({Path(file) for file in files})

    def pytest_terminal_summary(
        self, terminalreporter: pytest.TerminalReporter
    ) -> None:
        """Show the findings section after the test results."""
        if self.findings is None:
            return
        terminalreporter.write_sep("=", "drill sergeant")
        terminalreporter.write(
            render(
                self.findings,
                voice=self.resolved.voice,
                limit=self.resolved.max_findings,
            )
        )

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Fail a run whose tests ran and passed when a finding is at `fail` level."""
        if (
            session.exitstatus == pytest.ExitCode.OK
            and not self.config.option.collectonly
            and any(f.level is Level.FAIL for f in self.findings or ())
        ):
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
