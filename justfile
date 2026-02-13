# Development shortcuts for pytest-drill-sergeant

# Run tests
test:
    uv run pytest -q

# Run unit tests only
test-unit:
    uv run pytest tests -m unit

# Run integration tests only
test-integration:
    uv run pytest tests -m integration

# Run linting
lint:
    uv run ruff check src tests

# Run type checking
type-check:
    uv run mypy src tests --config-file=pyproject.toml

# Run all required quality checks (matches CI quality gates)
verify: test lint type-check

# Backwards-compatible alias
quality: verify

# Generate coverage report
coverage:
    uv run pytest tests --cov=src --cov-report=xml --cov-report=term-missing

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
    uv sync --all-extras

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
    just verify

# Test the plugin with a sample project
demo:
    clear || cls
    @echo "🎖️ Testing pytest-drill-sergeant plugin"
    @echo "🧪 Running tests with drill sergeant enforcement..."
    uv run pytest tests -v

# Show help
default:
    @just --list
