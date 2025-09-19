"""Example demonstrating advanced per-file configuration controls.

This example shows how to use the new per-file/per-path controls in
pytest-drill-sergeant configuration.
"""

# Example pyproject.toml configuration
PYPROJECT_TOML_EXAMPLE = """
[tool.pytest-drill-sergeant]
schema_version = "1.0"
profile = "standard"

# Basic file patterns
test_patterns = ["test_*.py", "tests/**/*.py", "specs/**/*.py"]
ignore_patterns = ["*_integration.py", "**/migrations/*.py"]

# Additional include/exclude patterns
include_patterns = ["**/test_*.py", "**/spec_*.py"]
exclude_patterns = ["**/legacy/*.py", "**/deprecated/*.py"]

# Per-file rule ignores
[tool.pytest-drill-sergeant.per_file_ignores]
"test_legacy.py" = ["DS201", "DS202"]  # Ignore duplicate and fixture rules
"test_old.py" = ["DS301"]  # Ignore private access rule
"**/integration/*.py" = ["DS201", "DS202", "DS301"]  # Ignore all rules in integration tests

# Per-file severity overrides
[tool.pytest-drill-sergeant.per_file_severity_overrides]
"test_critical.py" = "error"  # Make all findings errors
"test_warning.py" = "warning"  # Make all findings warnings
"**/production/*.py" = "error"  # Strict mode for production tests

# Per-file rule configuration overrides
[tool.pytest-drill-sergeant.per_file_rule_overrides]
"test_special.py" = {
    "DS201" = { enabled = false, severity = "info" },  # Disable duplicate test detection
    "DS202" = { threshold = 0.5, severity = "warning" },  # Lower threshold for fixture extraction
}
"**/performance/*.py" = {
    "DS301" = { enabled = false },  # Disable private access detection in performance tests
    "DS302" = { threshold = 0.3 },  # Lower threshold for AAA comment detection
}

# Global rule configurations
[tool.pytest-drill-sergeant.rules]
DS201 = { enabled = true, severity = "warning", threshold = 0.8 }
DS202 = { enabled = true, severity = "info", threshold = 0.6 }
DS301 = { enabled = true, severity = "warning" }
DS302 = { enabled = true, severity = "info", threshold = 0.7 }

# Analysis settings
[tool.pytest-drill-sergeant.analysis]
parallel = true
max_workers = 4
cache_ast = true
timeout = 30.0

# Output settings
[tool.pytest-drill-sergeant.output]
format = "terminal"
verbose = true
color = true
show_source = true
show_suggestions = true
"""

# Example pytest.ini configuration
PYTEST_INI_EXAMPLE = """
[pytest]
# ... other pytest configuration ...

[tool:pytest-drill-sergeant]
schema_version = 1.0
profile = strict

# File patterns
test_patterns = test_*.py
ignore_patterns = *_integration.py
include_patterns = tests/**/*.py
exclude_patterns = **/migrations/*.py

# Per-file ignores
per_file_ignores =
    test_legacy.py:DS201,DS202
    test_old.py:DS301
    **/integration/*.py:DS201,DS202,DS301

# Per-file severity overrides
per_file_severity_overrides =
    test_critical.py:error
    test_warning.py:warning
    **/production/*.py:error

# Per-file rule overrides (JSON format)
per_file_rule_overrides =
    test_special.py:{"DS201": {"enabled": false, "severity": "info"}, "DS202": {"threshold": 0.5}}
    **/performance/*.py:{"DS301": {"enabled": false}, "DS302": {"threshold": 0.3}}
"""

# Example environment variable configuration
ENV_VAR_EXAMPLE = """
# Environment variables for configuration
export DS_TEST_PATTERNS="test_*.py,tests/**/*.py"
export DS_IGNORE_PATTERNS="*_integration.py,**/migrations/*.py"
export DS_INCLUDE_PATTERNS="**/test_*.py,**/spec_*.py"
export DS_EXCLUDE_PATTERNS="**/legacy/*.py,**/deprecated/*.py"

# Per-file ignores (JSON format)
export DS_PER_FILE_IGNORES='{"test_legacy.py": ["DS201", "DS202"], "test_old.py": ["DS301"]}'

# Per-file severity overrides (JSON format)
export DS_PER_FILE_SEVERITY_OVERRIDES='{"test_critical.py": "error", "test_warning.py": "warning"}'

# Per-file rule overrides (JSON format)
export DS_PER_FILE_RULE_OVERRIDES='{"test_special.py": {"DS201": {"enabled": false, "severity": "info"}}}'
"""

# Example CLI usage
CLI_EXAMPLE = """
# Command line usage examples
pytest --ds-test-patterns="test_*.py,tests/**/*.py" --ds-ignore-patterns="*_integration.py"
pytest --ds-include-patterns="**/test_*.py" --ds-exclude-patterns="**/legacy/*.py"
pytest --ds-per-file-ignores='{"test_legacy.py": ["DS201", "DS202"]}'
pytest --ds-per-file-severity-overrides='{"test_critical.py": "error"}'
pytest --ds-per-file-rule-overrides='{"test_special.py": {"DS201": {"enabled": false}}}'
"""

# Example usage in Python code
PYTHON_USAGE_EXAMPLE = """
from pathlib import Path
from pytest_drill_sergeant.core.config_schema import DSConfig, SeverityLevel, RuleConfig
from pytest_drill_sergeant.core.file_discovery import create_file_discovery

# Create configuration with per-file controls
config = DSConfig(
    project_root=Path.cwd(),
    test_patterns=["test_*.py", "tests/**/*.py"],
    ignore_patterns=["*_integration.py"],
    include_patterns=["**/test_*.py", "**/spec_*.py"],
    exclude_patterns=["**/legacy/*.py", "**/deprecated/*.py"],
    per_file_ignores={
        "test_legacy.py": ["DS201", "DS202"],
        "test_old.py": ["DS301"],
        "**/integration/*.py": ["DS201", "DS202", "DS301"],
    },
    per_file_severity_overrides={
        "test_critical.py": SeverityLevel.ERROR,
        "test_warning.py": SeverityLevel.WARNING,
        "**/production/*.py": SeverityLevel.ERROR,
    },
    per_file_rule_overrides={
        "test_special.py": {
            "DS201": RuleConfig(enabled=False, severity=SeverityLevel.INFO),
            "DS202": RuleConfig(threshold=0.5, severity=SeverityLevel.WARNING),
        },
        "**/performance/*.py": {
            "DS301": RuleConfig(enabled=False),
            "DS302": RuleConfig(threshold=0.3),
        },
    },
)

# Create file discovery instance
file_discovery = create_file_discovery(config)

# Discover files to analyze
analysis_files = file_discovery.discover_files()
print(f"Found {len(analysis_files)} files to analyze")

# Check if a specific file should be analyzed
test_file = Path("test_example.py")
if file_discovery.should_analyze_file(test_file):
    print(f"Will analyze {test_file}")

    # Get file-specific configuration
    file_config = file_discovery.get_file_config(test_file)
    print(f"Ignored rules: {file_config['ignored_rules']}")
    print(f"Severity override: {file_config['severity_override']}")
    print(f"Rule overrides: {file_config['rule_overrides']}")

    # Check if specific rules are ignored
    if file_discovery.is_rule_ignored_for_file(test_file, "DS201"):
        print("DS201 is ignored for this file")

    # Get effective severity for a rule
    effective_severity = file_discovery.get_effective_severity(
        test_file, "DS201", SeverityLevel.WARNING
    )
    print(f"Effective severity for DS201: {effective_severity}")

    # Get effective rule configuration
    rule_config = file_discovery.get_effective_rule_config(test_file, "DS201")
    if rule_config:
        print(f"Rule DS201 enabled: {rule_config.enabled}")
        print(f"Rule DS201 severity: {rule_config.severity}")
        print(f"Rule DS201 threshold: {rule_config.threshold}")

# Get discovery statistics
stats = file_discovery.get_discovery_stats()
print(f"Discovery stats: {stats}")
"""

if __name__ == "__main__":
    print("Advanced Configuration Examples")
    print("=" * 50)
    print("\n1. pyproject.toml Configuration:")
    print(PYPROJECT_TOML_EXAMPLE)
    print("\n2. pytest.ini Configuration:")
    print(PYTEST_INI_EXAMPLE)
    print("\n3. Environment Variables:")
    print(ENV_VAR_EXAMPLE)
    print("\n4. CLI Usage:")
    print(CLI_EXAMPLE)
    print("\n5. Python Usage:")
    print(PYTHON_USAGE_EXAMPLE)
