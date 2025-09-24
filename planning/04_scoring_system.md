# Scoring System

## Overview

The scoring system provides two main metrics:
1. **Behavior Integrity Score (BIS)** - Per-test quality metric (0-100)
2. **Battlefield Readiness Score (BRS)** - Overall test suite quality metric (0-100)

## Behavior Integrity Score (BIS)

### Purpose
Measures how well a test focuses on **WHAT** the code does rather than **HOW** it works internally.

### Implementation Overview

The BIS system consists of three main components:

1. **DynamicBISCalculator**: Core scoring algorithm using rule metadata
2. **BISCalculator**: Main calculator integrating with plugin hooks
3. **TestFeatureExtractor**: AST-based feature extraction from test files

### Scoring Formula (Rule-Based Dynamic System)

The BIS uses a **dynamic rule-based penalty system** that reads impact and weights from rule definitions:

```python
class DynamicBISCalculator:
    """Dynamic BIS calculator that uses rule metadata for scoring."""
    
    # Base penalty weights by impact category
    PENALTY_WEIGHTS = {
        "high_penalty": 15.0,  # Major behavior integrity issues
        "medium_penalty": 8.0,  # Moderate behavior integrity issues
        "low_penalty": 4.0,  # Minor behavior integrity issues
        "advisory": 1.0,  # Style/structure issues (minimal)
        "reward": -5.0,  # Positive behavior indicators
    }

    def calculate_bis(self, metrics: BISMetrics) -> float:
        """Calculate Behavior Integrity Score based on metrics."""
        base_score = 100.0
        
        # Calculate penalties based on weighted counts
        total_penalty = 0.0
        
        # High penalty violations (major behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["high_penalty"] * min(
            metrics.weighted_high_penalty, 5.0
        )
        
        # Medium penalty violations (moderate behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["medium_penalty"] * min(
            metrics.weighted_medium_penalty, 8.0
        )
        
        # Low penalty violations (minor behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["low_penalty"] * min(
            metrics.weighted_low_penalty, 10.0
        )
        
        # Advisory violations (style/structure issues)
        total_penalty += self.PENALTY_WEIGHTS["advisory"] * min(
            metrics.weighted_advisory, 15.0
        )
        
        # Reward for positive behavior indicators
        reward = self.PENALTY_WEIGHTS["reward"] * min(metrics.weighted_reward, 3.0)
        
        # Calculate final score
        raw_score = base_score - total_penalty + reward
        
        return max(0, min(100, round(raw_score, 1)))
```

### Rule-Based Impact System

The BIS system uses rule metadata to determine impact categories and weights:

**Impact Categories**:
- **High Penalty (15.0)**: Major behavior integrity issues (DS301 - Private Access, DS305 - Mock Over-specification)
- **Medium Penalty (8.0)**: Moderate behavior integrity issues (DS306 - Structural Equality)
- **Low Penalty (4.0)**: Minor behavior integrity issues
- **Advisory (1.0)**: Style/structure issues (DS302 - AAA Comments)
- **Reward (-5.0)**: Positive behavior indicators

**Rule Configuration Example**:
```python
PRIVATE_ACCESS = RuleSpec(
    code="DS301",
    name="private_access",
    default_level=Severity.WARNING,
    short_desc="Detect access to private members in tests",
    long_desc="Flags tests that access private methods, attributes, or modules.",
    tags=["encapsulation", "quality", "brittleness"],
    fixable=False,
    category=RuleCategory.CODE_QUALITY,
    bis_impact=BISImpact.HIGH_PENALTY,  # High penalty for BIS
    bis_weight=1.5,  # Weight multiplier
)
```

### Mathematical Justification

**Penalty Weights** (based on test quality research):
- **High Penalty (15.0)**: Breaks encapsulation, creates tight coupling to implementation
- **Medium Penalty (8.0)**: Leads to brittle, hard-to-maintain tests
- **Low Penalty (4.0)**: Minor brittleness, easily fixed
- **Advisory (1.0)**: Style/structure issues, minimal impact

**Reward Calculation**:
- Uses negative weights to provide bonuses for positive behavior
- Capped at 3.0 to prevent score inflation

### Score Interpretation
- **85-100**: Excellent - Focuses on behavior, not implementation
- **70-84**: Good - Mostly behavior-focused with minor HOW smells
- **55-69**: Caution - Some implementation details leaking through
- **40-54**: Poor - Testing implementation details
- **0-39**: Critical - Heavily focused on internal workings

### BIS Implementation Architecture

The BIS system is implemented as a three-layer architecture:

#### 1. Feature Extraction Layer (`TestFeatureExtractor`)
```python
class TestFeatureExtractor:
    """Extracts features from test files for BIS calculation."""
    
    def extract_features_from_file(
        self, file_path: Path, findings: list[Finding]
    ) -> dict[str, FeaturesData]:
        """Extract features for all tests in a file."""
        # Parse AST and extract test functions
        # Count assertions, complexity, setup/teardown lines
        # Map findings to specific tests
```

#### 2. Core Calculation Layer (`DynamicBISCalculator`)
```python
class DynamicBISCalculator:
    """Core BIS calculator using rule metadata."""
    
    def extract_metrics_from_findings(self, findings: list[Finding]) -> BISMetrics:
        """Extract BIS metrics from analysis findings using rule metadata."""
        # Group findings by impact category
        # Apply rule-specific weights
        # Calculate weighted totals
```

#### 3. Integration Layer (`BISCalculator`)
```python
class BISCalculator:
    """Main BIS calculator integrating with plugin system."""
    
    def calculate_file_bis(
        self, file_path: Path, findings: list[Finding]
    ) -> dict[str, ResultData]:
        """Calculate BIS scores for all tests in a file."""
        # Use feature extractor to get test features
        # Use dynamic calculator for scoring
        # Store results for retrieval
```

### Feature Extraction

#### AST-Based Feature Analysis
```python
@dataclass
class FeaturesData:
    test_name: str
    file_path: Path
    line_number: int
    
    # AST-based features
    has_aaa_comments: bool = False
    private_access_count: int = 0
    mock_assertion_count: int = 0
    structural_equality_count: int = 0
    test_length: int = 0
    complexity_score: float = 0.0
    assertion_count: int = 0
    setup_lines: int = 0
    teardown_lines: int = 0
```

#### Mock Over-Specification
```python
@dataclass
class MockFeatures:
    assert_called_once: int = 0
    assert_called_with: int = 0
    assert_has_calls: int = 0
    assert_any_call: int = 0

    @property
    def total_count(self) -> int:
        return (self.assert_called_once + self.assert_called_with +
                self.assert_has_calls + self.assert_any_call)
```

#### Public API Assertions (Reward)
```python
@dataclass
class PublicAPIFeatures:
    return_value_assertions: int = 0
    public_attribute_assertions: int = 0
    public_method_assertions: int = 0

    @property
    def total_count(self) -> int:
        return (self.return_value_assertions +
                self.public_attribute_assertions +
                self.public_method_assertions)
```

## Battlefield Readiness Score (BRS)

### Purpose
Overall test suite quality metric that combines multiple quality dimensions.

### Scoring Formula
```python
def calculate_brs(metrics: RunMetrics) -> float:
    score = 100.0

    # AAA compliance (30% weight)
    score -= 30 * (1 - metrics.aaa_rate)

    # Duplicate tests penalty (20% weight)
    duplicate_penalty = min(1.0, metrics.duplicate_tests / max(1, metrics.total_tests))
    score -= 20 * duplicate_penalty

    # Parametrization rate (10% weight)
    score -= 10 * (1 - metrics.param_rate)

    # Fixture reuse rate (10% weight)
    score -= 10 * (1 - metrics.fixture_reuse_rate)

    # Non-determinism rate (10% weight)
    score -= 10 * metrics.non_determinism_rate

    # Slow tests rate (10% weight)
    score -= 10 * metrics.slow_tests_rate

    # Style smells rate (10% weight)
    score -= 10 * metrics.style_smell_rate

    return max(0, min(100, score))
```

### Component Metrics

#### AAA Rate
```python
def calculate_aaa_rate(test_results: List[TestResult]) -> float:
    """Calculate percentage of tests with proper AAA structure"""
    total_tests = len(test_results)
    if total_tests == 0:
        return 1.0

    aaa_compliant = sum(1 for result in test_results
                       if result.aaa_compliance == "excellent" or
                          result.aaa_compliance == "good")

    return aaa_compliant / total_tests
```

#### Duplicate Tests Penalty
```python
def calculate_duplicate_penalty(clusters: List[Cluster]) -> float:
    """Calculate penalty for duplicate tests"""
    total_duplicates = sum(len(cluster.members) for cluster in clusters)
    total_tests = sum(len(cluster.members) for cluster in clusters) + len(unique_tests)

    return min(1.0, total_duplicates / max(1, total_tests))
```

#### Parametrization Rate
```python
def calculate_param_rate(test_results: List[TestResult]) -> float:
    """Calculate percentage of tests that are parametrized"""
    total_tests = len(test_results)
    if total_tests == 0:
        return 1.0

    parametrized = sum(1 for result in test_results if result.is_parametrized)
    return parametrized / total_tests
```

#### Fixture Reuse Rate
```python
def calculate_fixture_reuse_rate(test_results: List[TestResult]) -> float:
    """Calculate how well tests reuse fixtures vs repeated setup"""
    total_setup_lines = 0
    fixture_usage_count = 0

    for result in test_results:
        total_setup_lines += result.arrange_lines
        if result.uses_fixtures:
            fixture_usage_count += 1

    # Simple heuristic: higher fixture usage = better reuse
    return fixture_usage_count / len(test_results) if test_results else 1.0
```

#### Non-Determinism Rate
```python
def calculate_nondeterminism_rate(test_results: List[TestResult]) -> float:
    """Calculate percentage of tests with non-deterministic elements"""
    total_tests = len(test_results)
    if total_tests == 0:
        return 0.0

    nondeterministic = sum(1 for result in test_results
                          if result.has_sleep or
                             result.has_random or
                             result.has_network_calls or
                             result.has_time_dependencies)

    return nondeterministic / total_tests
```

#### Slow Tests Rate
```python
def calculate_slow_tests_rate(test_results: List[TestResult], threshold: float = 5.0) -> float:
    """Calculate percentage of tests exceeding time threshold"""
    total_tests = len(test_results)
    if total_tests == 0:
        return 0.0

    slow_tests = sum(1 for result in test_results
                    if result.execution_time > threshold)

    return slow_tests / total_tests
```

#### Style Smell Rate
```python
def calculate_style_smell_rate(files_analyzed: List[Path], findings: List[Finding]) -> float:
    """Calculate percentage of files with style issues"""
    total_files = len(files_analyzed)
    if total_files == 0:
        return 0.0

    files_with_smells = set()
    for finding in findings:
        if finding.rule_id in ["bare-except", "wildcard-import", "print-in-src"]:
            files_with_smells.add(finding.path)

    return len(files_with_smells) / total_files
```

## Score Reporting

### BIS Reporting and Integration

#### Per-Test BIS Reporting
The BIS system integrates with pytest hooks to provide real-time scoring:

```python
def _inject_persona_feedback(report: pytest.TestReport) -> None:
    """Inject persona feedback into test reports."""
    bis_calculator = get_bis_calculator()
    
    # Get BIS score for this test
    test_name = report.nodeid.split("::")[-1]
    bis_score = bis_calculator.get_test_bis_score(test_name)
    
    # Add BIS score information to the message
    bis_message = persona_manager.on_bis_score(test_name, bis_score)
    if bis_message:
        message = f"{message}\n\n{bis_message}"
```

#### Terminal Summary Integration
```python
def _generate_persona_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Generate persona summary for terminal output."""
    bis_calculator = get_bis_calculator()
    bis_summary = bis_calculator.get_bis_summary()
    
    # Add BIS summary
    terminalreporter.write_sep("-", "BIS (Behavior Integrity Score) Summary")
    terminalreporter.write_line(f"Average BIS Score: {bis_summary['average_score']:.1f}")
    terminalreporter.write_line(f"Highest Score: {bis_summary['highest_score']:.1f}")
    terminalreporter.write_line(f"Lowest Score: {bis_summary['lowest_score']:.1f}")
    
    # Grade distribution
    terminalreporter.write_line("Grade Distribution:")
    for grade, count in bis_summary["grade_distribution"].items():
        if count > 0:
            terminalreporter.write_line(f"  {grade}: {count}")
```

#### BIS Result Data Structure
```python
@dataclass
class ResultData:
    test_name: str
    file_path: Path
    line_number: int
    
    # Analysis results
    findings: list[Finding]
    features: FeaturesData
    bis_score: float  # 0-100
    bis_grade: str  # "A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"
    
    # Status
    analyzed: bool
    error_message: str | None
    analysis_time: float
```

### BRS Summary Report
```python
@dataclass
class BRSReport:
    overall_score: float
    grade: str
    component_scores: Dict[str, float]
    top_improvements: List[str]
    trend: Optional[str]  # "improving", "declining", "stable"

    def generate_component_scores(self, metrics: RunMetrics) -> Dict[str, float]:
        return {
            "aaa_compliance": 100 * metrics.aaa_rate,
            "duplicate_management": 100 * (1 - self.duplicate_penalty),
            "parametrization": 100 * metrics.param_rate,
            "fixture_reuse": 100 * metrics.fixture_reuse_rate,
            "determinism": 100 * (1 - metrics.non_determinism_rate),
            "performance": 100 * (1 - metrics.slow_tests_rate),
            "style_quality": 100 * (1 - metrics.style_smell_rate)
        }
```

## Configuration

### BIS Thresholds
```toml
[tool.pytest_drill_sergeant.bis]
threshold_excellent = 85
threshold_good = 70
threshold_caution = 55
threshold_poor = 40
```

### BRS Weights
```toml
[tool.pytest_drill_sergeant.brs.weights]
aaa_rate = 0.30
duplicate_penalty = 0.20
param_rate = 0.10
fixture_reuse_rate = 0.10
non_determinism_rate = 0.10
slow_tests_rate = 0.10
style_smell_rate = 0.10
```

### Quality Gates
```toml
[tool.pytest_drill_sergeant.quality_gates]
min_brs_score = 70
max_brs_drop = 5
max_duplicate_increase = 10
min_aaa_rate = 0.75
```

## Historical Tracking

### Trend Analysis
```python
@dataclass
class TrendAnalysis:
    current_score: float
    previous_score: float
    trend_direction: str  # "up", "down", "stable"
    trend_magnitude: float
    significant_change: bool

    def analyze_trend(self, history: List[RunMetrics]) -> 'TrendAnalysis':
        if len(history) < 2:
            return TrendAnalysis(0, 0, "stable", 0, False)

        current = history[-1].brs_score
        previous = history[-2].brs_score
        change = current - previous

        magnitude = abs(change)
        direction = "up" if change > 0 else "down" if change < 0 else "stable"
        significant = magnitude > 5  # Configurable threshold

        return TrendAnalysis(current, previous, direction, magnitude, significant)
```

### Performance Metrics
- Score calculation time
- Memory usage during analysis
- Cache hit rates
- Analysis accuracy metrics
