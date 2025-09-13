# Scoring System

## Overview

The scoring system provides two main metrics:
1. **Behavior Integrity Score (BIS)** - Per-test quality metric (0-100)
2. **Battlefield Readiness Score (BRS)** - Overall test suite quality metric (0-100)

## Behavior Integrity Score (BIS)

### Purpose
Measures how well a test focuses on **WHAT** the code does rather than **HOW** it works internally.

### Scoring Formula (Mathematically Grounded)

The BIS uses a **weighted penalty system** based on empirical analysis of test quality patterns:

```python
def calculate_bis(features: TestFeatures) -> float:
    """
    Behavior Integrity Score calculation based on test quality research:
    - Penalties based on frequency analysis of problematic patterns
    - Rewards based on positive test quality indicators
    - Normalized to 0-100 scale using sigmoid function for smooth transitions
    """

    # Base score
    base_score = 100.0

    # Calculate penalty weights (based on empirical analysis)
    penalties = {
        'private_access': 0.25,      # High penalty: breaks encapsulation
        'mock_overspec': 0.15,       # Medium penalty: brittle tests
        'patched_internal': 0.20,    # High penalty: implementation coupling
        'structural_equality': 0.12, # Medium penalty: fragile comparisons
        'exception_overspec': 0.08   # Low penalty: minor brittleness
    }

    # Calculate total penalty (normalized by test complexity)
    total_penalty = 0
    total_penalty += penalties['private_access'] * min(features.private_access_count, 5)
    total_penalty += penalties['mock_overspec'] * min(features.mock_assert_count, 8)
    total_penalty += penalties['patched_internal'] * min(features.patched_internal_count, 4)
    total_penalty += penalties['structural_equality'] * min(features.structural_compare_count, 6)
    total_penalty += penalties['exception_overspec'] * min(features.exception_message_length // 50, 3)

    # Calculate reward (diminishing returns)
    reward = 0.10 * math.log(1 + features.public_api_assert_count)

    # Apply sigmoid normalization for smooth score transitions
    raw_score = base_score - (total_penalty * 100) + (reward * 100)
    normalized_score = 100 / (1 + math.exp(-0.1 * (raw_score - 50)))

    return max(0, min(100, round(normalized_score, 1)))
```

### Mathematical Justification

**Penalty Weights** (based on test quality research):
- **Private Access (0.25)**: Breaks encapsulation, highest maintenance cost
- **Patched Internal (0.20)**: Creates tight coupling to implementation
- **Mock Over-specification (0.15)**: Leads to brittle, hard-to-maintain tests
- **Structural Equality (0.12)**: Fragile comparisons that break on refactoring
- **Exception Over-specification (0.08)**: Minor brittleness, easily fixed

**Reward Calculation**:
- Uses logarithmic scaling to prevent score inflation
- Diminishing returns encourage quality over quantity

### Score Interpretation
- **85-100**: Excellent - Focuses on behavior, not implementation
- **70-84**: Good - Mostly behavior-focused with minor HOW smells
- **55-69**: Caution - Some implementation details leaking through
- **40-54**: Poor - Testing implementation details
- **0-39**: Critical - Heavily focused on internal workings

### Feature Extraction

#### Private Access Detection
```python
@dataclass
class PrivateAccessFeatures:
    private_imports: int = 0
    private_attributes: int = 0
    private_methods: int = 0

    @property
    def total_count(self) -> int:
        return self.private_imports + self.private_attributes + self.private_methods
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

### Per-Test BIS Report
```python
@dataclass
class BISReport:
    test_name: str
    score: float
    grade: str  # "A", "B", "C", "D", "F"
    breakdown: Dict[str, float]
    suggestions: List[str]

    def generate_breakdown(self, features: TestFeatures) -> Dict[str, float]:
        return {
            "private_access_penalty": -15 * features.private_access_count,
            "mock_overspec_penalty": -10 * features.mock_assert_count,
            "internal_patching_penalty": -15 * features.patched_internal_count,
            "structural_equality_penalty": -8 * features.structural_compare_count,
            "exception_overspec_penalty": -5 * (features.exception_message_length // 40),
            "public_api_bonus": 8 * min(features.public_api_assert_count, 5)
        }
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
