# Technical Specifications

## System Requirements

### Python Version Support

**Why Python 3.10+?**
- **Pattern Matching**: Python 3.10 introduced structural pattern matching (`match/case`) which is useful for AST analysis
- **Union Types**: Better type hints with `X | Y` syntax instead of `Union[X, Y]`
- **Parenthesized Context Managers**: Cleaner syntax for multiple context managers
- **Performance**: Python 3.10+ has significant performance improvements
- **Ecosystem**: Most modern Python tools require 3.10+

**Version Strategy**:
- **Minimum**: Python 3.10 (required for core features)
- **Recommended**: Python 3.11+ (better performance, newer features)
- **Testing**: Python 3.10, 3.11, 3.12 (ensure compatibility)
- **EOL**: Python 3.9 reaches end-of-life in October 2025

### Dependencies

#### Core Dependencies
```toml
[project]
dependencies = [
    "pytest>=8.4.0",      # Latest stable with modern features
    "coverage>=7.1.0",    # Latest with improved performance and APIs
    "datasketch>=1.6.0",  # For MinHash/LSH
    "typer>=0.9.0",       # For CLI (modern, type-safe alternative to click)
    "pydantic>=2.0.0",    # For data validation
    "rich>=13.0.0",       # For terminal output
]
```

#### Optional Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.4.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]
ci = [
    "github-actions-toolkit>=0.1.0",
    "sarif-tools>=0.1.0",
]
lsp = [
    "pygls>=1.0.0",        # Language Server Protocol implementation
    "pygls-protocol>=1.0.0", # LSP protocol definitions
]
```

### Performance Requirements
- **Static Analysis**: < 100ms per test file
- **Runtime Analysis**: < 50ms overhead per test
- **Memory Usage**: < 100MB for typical test suites (< 1000 tests)
- **Startup Time**: < 500ms for plugin initialization

## Data Models

### Core Models

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Any
from pathlib import Path
from enum import Enum

class Severity(Enum):
    ADVICE = "advice"
    WARN = "warn"
    ERROR = "error"

@dataclass
class Finding:
    """Represents a single analysis finding"""
    rule_id: str
    severity: Severity
    path: Path
    location: Optional[tuple[int, int]]  # (line, column)
    message: str
    test_nodeid: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class Cluster:
    """Represents a cluster of similar tests"""
    kind: str  # "static" or "dynamic"
    members: List[str]  # Test nodeids
    similarity: float
    representative: Optional[str] = None
    suggestions: Optional[Dict[str, Any]] = None

@dataclass
class Rule:
    """Represents an analysis rule"""
    id: str
    category: str
    default_severity: Severity
    description: str
    enabled: bool = True
    config: Optional[Dict[str, Any]] = None

@dataclass
class TestFeatures:
    """Features extracted from a test for BIS calculation"""
    # HOW smells (penalties)
    private_access_count: int = 0
    mock_assert_count: int = 0
    patched_internal_count: int = 0
    structural_compare_count: int = 0
    exception_message_length: int = 0

    # WHAT behaviors (rewards)
    public_api_assert_count: int = 0

    # Additional metrics
    covered_lines: int = 0
    assert_count: int = 0
    arrange_lines: int = 0
    uses_fixtures: bool = False
    is_parametrized: bool = False

@dataclass
class RunMetrics:
    """Metrics for a complete test run"""
    total_tests: int
    aaa_rate: float
    duplicate_tests: int
    duplicate_clusters: int
    param_rate: float
    fixture_reuse_rate: float
    non_determinism_rate: float
    slow_tests_rate: float
    style_smell_rate: float
    bis_stats: Dict[str, float]  # mean, median, p90, etc.
    car_histogram: Dict[str, int]
    clusters: List[Cluster]

@dataclass
class TestResult:
    """Result of analyzing a single test"""
    nodeid: str
    bis_score: float
    bis_grade: str
    features: TestFeatures
    findings: List[Finding]
    execution_time: Optional[float] = None
    aaa_compliance: Optional[str] = None

@dataclass
class Config:
    """Configuration for the plugin"""
    mode: str = "advisory"  # advisory | quality-gate | strict
    persona: str = "drill_sergeant"
    sut_package: Optional[str] = None
    budgets: Dict[str, int] = None
    enabled_rules: Set[str] = None
    suppressed_rules: Set[str] = None
    thresholds: Dict[str, float] = None
    mock_allowlist: Set[str] = None

    def __post_init__(self):
        if self.budgets is None:
            self.budgets = {"warn": 25, "error": 0}
        if self.enabled_rules is None:
            self.enabled_rules = {"aaa-comments", "static-clones", "fixture-extract"}
        if self.suppressed_rules is None:
            self.suppressed_rules = set()
        if self.thresholds is None:
            self.thresholds = {
                "static_clone_hamming": 6,
                "dynamic_cov_jaccard": 0.95,
                "bis_threshold_warn": 80,
                "bis_threshold_fail": 65
            }
        if self.mock_allowlist is None:
            self.mock_allowlist = {"requests.*", "boto3.*", "time.*", "random.*"}
```

## API Specifications

### Pytest Plugin API

```python
# Main plugin entry point
def pytest_addoption(parser):
    """Add command line options"""
    group = parser.getgroup("drill-sergeant")
    group.addoption(
        "--ds-mode",
        action="store",
        choices=["advisory", "quality-gate", "strict"],
        default="advisory",
        help="Drill sergeant mode"
    )
    group.addoption(
        "--ds-persona",
        action="store",
        default="drill_sergeant",
        help="Persona to use for feedback"
    )
    group.addoption(
        "--ds-sut-package",
        action="store",
        help="System under test package name"
    )
    group.addoption(
        "--ds-fail-on-how",
        action="store_true",
        help="Fail tests with low BIS scores"
    )
    group.addoption(
        "--ds-json-report",
        action="store",
        help="Path to JSON report output"
    )
    group.addoption(
        "--ds-sarif-report",
        action="store",
        help="Path to SARIF report output"
    )

def pytest_configure(config):
    """Configure the plugin"""
    config._drill_sergeant = DrillSergeantPlugin(config)

def pytest_collection_modifyitems(session, config, items):
    """Modify test items during collection"""
    plugin = config._drill_sergeant
    plugin.analyze_test_collection(items)

def pytest_runtest_setup(item):
    """Setup before each test runs"""
    plugin = item.config._drill_sergeant
    plugin.setup_test(item)

def pytest_runtest_call(item):
    """Execute the test with analysis"""
    plugin = item.config._drill_sergeant
    plugin.execute_test(item)

def pytest_runtest_logreport(report):
    """Process test report"""
    plugin = report.config._drill_sergeant
    plugin.process_test_report(report)

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate terminal summary"""
    plugin = config._drill_sergeant
    plugin.generate_summary(terminalreporter, exitstatus)

def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session"""
    plugin = session.config._drill_sergeant
    plugin.finalize_session(exitstatus)
```

### CLI API

**Why Typer over Click?**
- **Type Safety**: Full type hints support, catches errors at development time
- **Modern Python**: Uses modern Python features (dataclasses, type hints)
- **Better DX**: Auto-generated help, validation, and error messages
- **Less Boilerplate**: Cleaner, more Pythonic syntax
- **Rich Integration**: Built-in support for Rich library (colors, tables, progress bars)

```python
import typer
from typing import List, Optional
from pathlib import Path

app = typer.Typer(help="pytest-drill-sergeant: AI test quality enforcement")

@app.command()
def lint(
    paths: List[Path] = typer.Argument(..., help="Test files or directories to analyze"),
    output_format: str = typer.Option("terminal", "--format", "-f", help="Output format"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file"),
    persona: str = typer.Option("drill_sergeant", "--persona", help="Persona to use"),
    sut_package: Optional[str] = typer.Option(None, "--sut-package", help="SUT package name")
):
    """Analyze test files for quality issues"""
    # Implementation here

@app.command()
def demo(
    persona: str = typer.Option("drill_sergeant", "--persona", help="Persona to use")
):
    """Run a demo of the plugin with sample tests"""
    pass

@app.command()
def personas():
    """List available personas"""
    pass

if __name__ == "__main__":
    app()
```

### Configuration Strategy

**Why pyproject.toml + pytest.ini?**
- **pyproject.toml**: Modern Python standard, used by build tools, supports complex configurations
- **pytest.ini**: Legacy compatibility, simpler for basic settings, familiar to pytest users

**Configuration Hierarchy** (highest to lowest priority):
1. Command line arguments (`--ds-mode=strict`)
2. Environment variables (`DRILL_SERGEANT_MODE=strict`)
3. pytest.ini (`[tool:pytest-drill-sergeant]`)
4. pyproject.toml (`[tool.pytest-drill-sergeant]`)
5. Default values

**Example pytest.ini** (simple):
```ini
[tool:pytest-drill-sergeant]
mode = advisory
persona = drill_sergeant
sut_package = myapp
```

**Example pyproject.toml** (complex):
```toml
[tool.pytest-drill-sergeant]
mode = "quality-gate"
persona = "snoop_dogg"
budgets = { warn = 25, error = 0 }
rules = { enable = ["aaa-comments", "static-clones"] }
```

### Core Analysis API

```python
class AnalysisPipeline:
    """Main analysis pipeline"""

    def __init__(self, config: Config):
        self.config = config
        self.analyzers: List[Analyzer] = []
        self._setup_analyzers()

    def analyze_file(self, file_path: Path) -> List[Finding]:
        """Analyze a single test file"""
        findings = []
        for analyzer in self.analyzers:
            findings.extend(analyzer.analyze(file_path))
        return findings

    def analyze_collection(self, test_files: List[Path]) -> Dict[str, List[Finding]]:
        """Analyze a collection of test files"""
        results = {}
        for file_path in test_files:
            results[str(file_path)] = self.analyze_file(file_path)
        return results

class Analyzer(ABC):
    """Base class for analyzers"""

    @abstractmethod
    def analyze(self, file_path: Path) -> List[Finding]:
        """Analyze a file and return findings"""
        pass

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Return the rule ID for this analyzer"""
        pass

class CloneDetector:
    """Detect duplicate tests"""

    def __init__(self, config: Config):
        self.config = config
        self.simhash_threshold = config.thresholds["static_clone_hamming"]
        self.jaccard_threshold = config.thresholds["dynamic_cov_jaccard"]

    def find_static_clones(self, test_files: List[Path]) -> List[Cluster]:
        """Find static duplicates using AST similarity"""
        pass

    def find_dynamic_clones(self, coverage_data: Dict[str, Set[int]]) -> List[Cluster]:
        """Find dynamic duplicates using coverage similarity"""
        pass

class FixtureExtractor:
    """Extract fixture suggestions"""

    def find_arrange_patterns(self, test_files: List[Path]) -> List[FixtureSuggestion]:
        """Find repeated arrange patterns"""
        pass

    def generate_fixture_suggestion(self, pattern: ArrangePattern) -> FixtureSuggestion:
        """Generate a fixture suggestion from a pattern"""
        pass
```

## File Format Specifications

### JSON Report Format

```json
{
  "version": "1.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "run_id": "abc123",
  "config": {
    "mode": "advisory",
    "persona": "drill_sergeant",
    "sut_package": "myapp"
  },
  "metrics": {
    "total_tests": 150,
    "brs_score": 78.5,
    "aaa_rate": 0.82,
    "duplicate_tests": 12,
    "duplicate_clusters": 3,
    "param_rate": 0.45,
    "fixture_reuse_rate": 0.67,
    "non_determinism_rate": 0.08,
    "slow_tests_rate": 0.12,
    "style_smell_rate": 0.05
  },
  "bis_distribution": {
    "mean": 72.3,
    "median": 75.0,
    "p90": 88.0,
    "p95": 92.0
  },
  "findings": [
    {
      "rule_id": "private-access",
      "severity": "warn",
      "path": "tests/test_user.py",
      "location": [45, 12],
      "message": "Accessing private attribute: _internal_state",
      "test_nodeid": "tests/test_user.py::test_user_creation"
    }
  ],
  "clusters": [
    {
      "kind": "static",
      "members": [
        "tests/test_user.py::test_valid_name_alice",
        "tests/test_user.py::test_valid_name_bob",
        "tests/test_user.py::test_valid_name_charlie"
      ],
      "similarity": 0.95,
      "suggestions": {
        "parametrize": {
          "parameter": "name",
          "values": ["alice", "bob", "charlie"]
        }
      }
    }
  ],
  "fixture_suggestions": [
    {
      "fixture_name": "user_with_orders",
      "usage_count": 4,
      "original_tests": [
        "tests/test_orders.py::test_order_creation",
        "tests/test_orders.py::test_order_update"
      ],
      "fixture_code": "@pytest.fixture\ndef user_with_orders(order_count=3):\n    # ..."
    }
  ]
}
```

### SARIF Report Format

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "pytest-drill-sergeant",
          "version": "1.0.0",
          "informationUri": "https://github.com/your-org/pytest-drill-sergeant"
        }
      },
      "results": [
        {
          "ruleId": "private-access",
          "level": "warning",
          "message": {
            "text": "Accessing private attribute: _internal_state"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "tests/test_user.py"
                },
                "region": {
                  "startLine": 45,
                  "startColumn": 12
                }
              }
            }
          ],
          "properties": {
            "test_nodeid": "tests/test_user.py::test_user_creation",
            "bis_score": 65.0,
            "severity": "warn"
          }
        }
      ]
    }
  ]
}
```

## Configuration Schema

### pyproject.toml Schema

```toml
[tool.pytest_drill_sergeant]
# Mode: advisory (default), quality-gate, strict
mode = "advisory"

# Persona: drill_sergeant (default), snoop_dogg, motivational_coach, etc.
persona = "drill_sergeant"

# System under test package (auto-detected if not specified)
sut_package = "myapp"

# Budgets for quality-gate mode
[tool.pytest_drill_sergeant.budgets]
warn = 25
error = 0

# Enabled rules
[tool.pytest_drill_sergeant.rules]
enable = [
    "aaa-comments",
    "static-clones",
    "fixture-extract",
    "behavior-integrity",
    "mock-overspec",
    "private-access"
]
suppress = []

# Thresholds for various algorithms
[tool.pytest_drill_sergeant.thresholds]
static_clone_hamming = 6
dynamic_cov_jaccard = 0.95
bis_threshold_warn = 80
bis_threshold_fail = 65
slow_test_threshold = 5.0

# Mock allowlist for legitimate mock targets
[tool.pytest_drill_sergeant.mock_allowlist]
allowed = [
    "requests.*",
    "boto3.*",
    "time.*",
    "random.*",
    "os.*",
    "subprocess.*"
]

# BRS scoring weights
[tool.pytest_drill_sergeant.brs.weights]
aaa_rate = 0.30
duplicate_penalty = 0.20
param_rate = 0.10
fixture_reuse_rate = 0.10
non_determinism_rate = 0.10
slow_tests_rate = 0.10
style_smell_rate = 0.10

# Quality gates
[tool.pytest_drill_sergeant.quality_gates]
min_brs_score = 70
max_brs_drop = 5
max_duplicate_increase = 10
min_aaa_rate = 0.75

# Persona-specific settings
[tool.pytest_drill_sergeant.personas]
drill_sergeant.intensity = "high"
snoop_dogg.coolness_factor = "maximum"
motivational_coach.enthusiasm = "extreme"
```

## Performance Specifications

### Memory Usage
- **Base**: 50MB for plugin initialization
- **Per Test File**: 1MB for AST analysis
- **Coverage Data**: 0.5MB per 100 tests
- **Total Limit**: 200MB for test suites up to 2000 tests

### CPU Usage
- **Static Analysis**: 50ms per test file (average)
- **Runtime Overhead**: 10ms per test (average)
- **Parallel Processing**: 4x speedup with 4 cores

### Disk Usage
- **Cache**: 10MB for typical project
- **Reports**: 1MB per 1000 tests
- **Temporary Files**: 5MB during analysis

## Compatibility Matrix

**Why a Compatibility Matrix?**
- **Real Compatibility Issues**: Different pytest versions have breaking changes in plugin APIs
- **Coverage.py Changes**: Coverage collection APIs change between versions
- **Python Version Support**: Some features require specific Python versions
- **CI/CD Integration**: Different platforms have different capabilities

### Pytest Versions (Real Compatibility Requirements)
| pytest-drill-sergeant | pytest | Python | Notes |
|----------------------|--------|--------|-------|
| 1.0.x | 8.4+ | 3.10+ | Latest stable, modern features |
| 1.1.x | 8.4+ | 3.10+ | Bug fixes, new features |
| 2.0.x | 8.5+ | 3.11+ | Future breaking changes |

### Coverage.py Versions (API Dependencies)
| pytest-drill-sergeant | coverage.py | Notes |
|----------------------|-------------|-------|
| 1.0.x | 7.1+ | Latest with improved performance |
| 1.1.x | 7.1+ | Enhanced dynamic context support |
| 2.0.x | 7.2+ | Future API improvements |

**Why Latest Versions?**
- **AI Coding Users**: Primarily modern codebases, not legacy systems
- **Performance**: Latest pytest/coverage have significant performance improvements
- **Features**: Modern APIs and capabilities we need for advanced analysis
- **Maintenance**: Easier to support fewer versions, focus on modern ecosystem

### CI/CD Platforms (Tested Integrations)
- **GitHub Actions**: ✅ Full support with SARIF upload
- **GitLab CI**: ✅ Full support with SARIF reports
- **Jenkins**: ✅ Full support with SARIF plugin
- **Azure DevOps**: ✅ Full support with SARIF publishing
- **CircleCI**: ✅ Full support with SARIF artifacts

**Note**: This matrix is based on actual testing, not theoretical compatibility.
