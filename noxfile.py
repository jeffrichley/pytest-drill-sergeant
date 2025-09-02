"""Nox automation file for pytest-drill-sergeant.

Key features:
- Uses `uv` for dependency installation.
- Supports Python 3.12+ (tests run on all versions, quality gates use 3.12).
- Sessions: tests, lint, type_check, precommit, coverage_html, complexity, security, pyproject.
- Re-uses local virtualenvs for speed; CI passes `--force-python` to isolate.

Following the Redwing Core pattern.
"""

from pathlib import Path

import nox

# -------- Global config -------- #
# Default to 3.12 for local development speed, but support 3.12+ for CI
PYTHON_VERSIONS = ["3.12", "3.13"]
DEFAULT_PYTHON = "3.12"  # Used by quality gates and local development

nox.options.sessions = [
    f"tests-{DEFAULT_PYTHON}",  # Only test on default Python locally
    "lint",
    "type_check", 
    "complexity",
    "security",
    "pyproject",
]
# Re-use existing venvs locally for speed; CI can override with --no-reuse-existing-virtualenvs
nox.options.reuse_existing_virtualenvs = True

PROJECT_ROOT = Path(__file__).parent


def install_project(session):
    """Install the project with uv and dev extras."""
    session.run("uv", "pip", "install", "-q", "-e", ".[dev]", external=True)
    # Always install core test dependencies
    session.run(
        "uv",
        "pip",
        "install",
        "-q",
        "pytest",
        "pytest-cov",
        "pytest-asyncio",
        "hypothesis",
        external=True,
    )


# -------- Sessions -------- #


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run pytest with coverage."""
    install_project(session)
    session.run(
        "pytest",
        "tests",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=xml",  # Generate XML for Codecov
        external=True,
    )


@nox.session(python=DEFAULT_PYTHON)
def lint(session):
    """Run Ruff autofix + Black autofix."""
    session.run("uv", "pip", "install", "-q", "ruff", "black", external=True)
    session.run("ruff", "check", "src", "tests", "--fix", "--config=pyproject.toml")
    session.run("black", "src", "tests", "--config=pyproject.toml")


@nox.session(python=DEFAULT_PYTHON)
def type_check(session):
    """Run MyPy type checks."""
    install_project(session)
    session.run("mypy", "src", "tests", "--config-file=pyproject.toml")


@nox.session(python=DEFAULT_PYTHON, name="pre-commit")
def precommit_hooks(session):
    """Run pre-commit hooks on all files."""
    session.run("uv", "pip", "install", "-q", "pre-commit", external=True)
    session.run("pre-commit", "run", "--all-files")


@nox.session(python=DEFAULT_PYTHON)
def coverage_html(session):
    """Generate an HTML coverage report."""
    session.run("uv", "pip", "install", "-q", "coverage[toml]", external=True)
    session.run("coverage", "html")
    html_path = PROJECT_ROOT / "htmlcov" / "index.html"
    session.log(f"Generated coverage HTML at {html_path.as_uri()}")


# ---------------- Extra quality sessions ---------------- #


@nox.session(python=DEFAULT_PYTHON)
def complexity(session):
    """Fail if cyclomatic complexity exceeds score B."""
    session.run("uv", "pip", "install", "-q", "xenon", external=True)
    # Tweak --max-absolute (A=0, B=10, C=20) to your tolerance
    session.run("xenon", "--max-absolute", "B", "src")


@nox.session(python=DEFAULT_PYTHON)
def security(session):
    """Run pip-audit against project dependencies."""
    session.run("uv", "pip", "install", "-q", "pip-audit", external=True)
    # Audit direct + transitive deps pinned in uv.lock
    session.run("pip-audit", "--progress-spinner=off")


@nox.session(python=DEFAULT_PYTHON)
def pyproject(session):
    """Validate pyproject.toml configuration."""
    session.run("uv", "pip", "install", "-q", "-e", ".", external=True)
    session.run("uv", "pip", "install", "-q", "validate-pyproject", external=True)
    session.run("validate-pyproject", "pyproject.toml")
