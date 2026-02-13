# Decision Log

Purpose: capture project-level decisions that affect behavior, scope, and maintenance.

## 2026-02-13: Remove Runtime Return-Type Enforcement

### Decision

- Removed plugin runtime return-type rule and auto-fix behavior.
- Standardized on Ruff annotations (`ANN`) for return-type enforcement.

### Why

- Return annotations are better enforced by static tools than runtime test hooks.
- Avoid duplicated responsibility between plugin and lint/typecheck stack.
- Reduces plugin complexity and surprise side effects.

### Impact

- Removed return-type validator and related config options.
- Added Ruff `ANN` selection in lint policy.
- `ruff check --fix` is the preferred auto-fix path.

## 2026-02-13: CI Contract Simplification

### Decision

- Required checks reduced to explicit gates:
  - tests
  - ruff lint
  - mypy typecheck
- Coverage remains informational.

### Why

- Faster CI feedback and lower operational noise.
- Better local/CI parity with `just verify`.

### Impact

- Removed Nox-driven CI orchestration.
- Removed low-signal stats workflow from required path.
- Established deterministic quality gate contract in README.

## 2026-02-13: Config Precedence Contract

### Decision

Final precedence is:

1. Environment variables
2. Pytest config (`pytest.ini` / `[tool.pytest.ini_options]`)
3. `[tool.drill_sergeant]` in `pyproject.toml`
4. Defaults

### Why

- Makes behavior predictable and easy to reason about.
- Supports project defaults with targeted overrides.

### Impact

- Config loading consolidated and covered by tests.
- README and tests aligned to this precedence model.
