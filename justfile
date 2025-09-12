# Development shortcuts for pytest-drill-sergeant
# Following the Redwing Core pattern

# Run tests
test:
    uv run pytest tests

# Run unit tests only
test-unit:
    uv run pytest tests -m unit

# Run integration tests only
test-integration:
    uv run pytest tests -m integration

# Run linting
lint:
    nox -s lint

# Run type checking
type-check:
    nox -s type_check

# Run all quality checks (matches CI quality gates)
quality: lint type-check complexity security pyproject

# Run comprehensive quality checks (includes AI-specific checks)
quality-full:
    nox -s dead_code imports docs_coverage duplication maintainability test_quality dependencies security_advanced

# Run quality checks with unsafe fixes enabled
quality-unsafe:
    @echo "🚨 Running quality checks with unsafe fixes..."
    uv run ruff check src tests --fix --unsafe-fixes
    uv run black src tests
    uv run mypy src tests --config-file=pyproject.toml

# Generate coverage report
coverage:
    nox -s coverage_html

# Run security audit
security:
    nox -s security

# Run complexity analysis
complexity:
    nox -s complexity

# Validate pyproject.toml
pyproject:
    nox -s pyproject

# Run pre-commit hooks
pre-commit:
    nox -s pre-commit

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
    rm -rf .nox
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
