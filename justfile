# Development shortcuts for pytest-drill-sergeant
# Following the Redwing Core pattern

# Run tests with coverage
test:
    uv run pytest tests --cov=src/pytest_drill_sergeant --cov-report=term-missing --cov-report=html

# Run tests without coverage (faster)
test-fast:
    uv run pytest tests

# Run unit tests only
test-unit:
    uv run pytest tests -m unit --cov=src/pytest_drill_sergeant --cov-report=term-missing --cov-report=html

# Run integration tests only
test-integration:
    uv run pytest tests -m integration --cov=src/pytest_drill_sergeant --cov-report=term-missing --cov-report=html

# Run linting
lint:
    uv run ruff check src tests --fix --config=pyproject.toml
    uv run black src tests --config=pyproject.toml

# Run type checking
type-check:
    uv run mypy src tests --config-file=pyproject.toml

# Run all quality checks (matches CI quality gates)
quality: lint type-check complexity

# Run comprehensive quality checks (includes AI-specific checks)
quality-full:
    uv run vulture src --min-confidence 80
    uv run isort src tests --check-only --diff
    uv run interrogate src --fail-under 80 --ignore-init-method
    uv run pylint src --disable=all --enable=duplicate-code
    uv run radon mi src --min B
    uv run pytest tests --benchmark-only --benchmark-skip
    uv run pipdeptree --warn fail
    uv run safety check --json
    uv run bandit -r src -f json
    uv run semgrep --config=auto src

# Run quality checks with unsafe fixes enabled
quality-unsafe:
    @echo "🚨 Running quality checks with unsafe fixes..."
    uv run ruff check src tests --fix --unsafe-fixes
    uv run black src tests
    uv run mypy src tests --config-file=pyproject.toml

# Generate coverage report
coverage:
    uv run coverage html
    @echo "Generated coverage HTML at htmlcov/index.html"

# Run security audit
security:
    uv run pip-audit --progress-spinner=off

# Run complexity analysis
complexity:
    uv run xenon --max-absolute B src

# Validate pyproject.toml
pyproject:
    uv run validate-pyproject pyproject.toml

# Run pre-commit hooks
pre-commit:
    uv run pre-commit run --all-files

# Install development dependencies
install:
    uv sync --group dev --all-extras

# Install test dependencies only
install-test:
    uv sync --extra test

# Install all dependencies (dev + test)
install-all:
    uv sync --all-extras

# Sync dependencies (reinstall all)
sync:
    uv sync --reinstall

# Clean up generated files
clean:
    rm -rf htmlcov
    rm -rf .pytest_cache
    rm -rf .mypy_cache
    rm -rf .ruff_cache

# Quick development workflow: clear screen, test, quality
j:
    clear || cls
    just test
    just quality

# Test the plugin with a sample project
demo:
    clear || cls
    @echo "🎖️ Testing pytest-drill-sergeant plugin"
    @echo "🧪 Running tests with drill sergeant enforcement..."
    uv run pytest tests -v

# Show help
default:
    @just --list
