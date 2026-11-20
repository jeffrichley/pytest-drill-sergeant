# Windows uses PowerShell, Unix-like systems use sh
set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
set shell := ["sh", "-cu"]

# `just check` is the gate. People, agents and CI run this one recipe, in this order,
# and each step fails the whole. The workflow names no tool this file does not, which is
# what makes green here mean green in CI.
check: lint format-check typecheck vulture test

# The auto-fixing half of the gate.
fix: lint-fix format

# One shared .venv at the repo root.
sync:
    uv sync --group dev

# --- The gate's steps -------------------------------------------------------------

lint:
    uv run ruff check

lint-fix:
    uv run ruff check --fix

format:
    uv run ruff format

format-check:
    uv run ruff format --check

typecheck:
    uv run mypy

vulture:
    uv run vulture

# The whole suite, with the coverage floor. A single file is `uv run pytest tests/x.py`,
# which measures nothing and so can never fail on the floor. Four workers, not `auto`:
# each builds its own session fixtures, and one per core swamps a big machine.
test:
    uv run pytest -q -n 4 --cov --cov-report=term

# --- Not the gate -----------------------------------------------------------------

# The suite five times over, shuffled, to find flakes before a run does.
stress count="5":
    uv run pytest -q -n 4 --count={{count}} --junitxml=stress-report.xml

# The speed budget: a warm run with nothing changed, over the committed 300-file
# suite. Not in the gate (timings belong to the machine), so CI runs it as its own
# job.
perf:
    uv run pytest -q -p no:randomly -m perf tests/perf

# The commit hooks: the fast checks before a commit, the message convention on it.
install-hooks:
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg
