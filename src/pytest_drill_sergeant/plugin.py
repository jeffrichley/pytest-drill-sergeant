"""The pytest plugin, registered through the `pytest11` entry point.

Installing the package turns it on; `-p no:drill_sergeant` or
`drill_sergeant_mode = off` turns it off. After collection it analyses the files that
contributed collected tests, once, on the xdist controller only; the tests then run as
always. The findings section after the test results shows them, and a run
whose tests pass exits 1 when any finding is at the `fail` level.
"""

from pathlib import Path

import pytest

from pytest_drill_sergeant.config import OPTIONS, Config, ConfigError, resolve
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


def _config(config: pytest.Config) -> Config:
    """The resolved drill-sergeant config.

    Raises:
        pytest.UsageError: When the config is wrong, naming what in one line.
    """
    try:
        raw = {option.name: config.getini(option.name) for option in OPTIONS}
        root = config.inipath.parent if config.inipath else config.rootpath
        return resolve(raw, root=root)
    except (ConfigError, ValueError, TypeError) as error:
        raise pytest.UsageError(f"drill-sergeant: {error}") from None


def pytest_configure(config: pytest.Config) -> None:
    """Resolve the config and, unless the mode is `off`, start the run.

    An xdist worker only runs tests, so it starts no run; the controller analyses.
    """
    resolved = _config(config)
    if resolved.mode is not Level.OFF and not hasattr(config, "workerinput"):
        config.pluginmanager.register(_Run(config, resolved), _RUN)


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
        self._analyze(
            {item.path for item in session.items if item.path.suffix == ".py"}
        )

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_node_collection_finished(self, ids: list[str]) -> None:
        """Analyse the files an xdist worker collected tests from (controller only)."""
        root = self.config.rootpath
        self._analyze(
            {
                (root / file).resolve()
                for file in (node_id.split("::")[0] for node_id in ids)
                if file.endswith(".py")
            }
        )

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
        """Fail a passing run when any finding is at the `fail` level."""
        if session.exitstatus == pytest.ExitCode.OK and any(
            f.level is Level.FAIL for f in self.findings or ()
        ):
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
