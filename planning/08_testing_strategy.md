# Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for pytest-drill-sergeant, covering unit tests, integration tests, performance tests, and quality assurance processes.

## Testing Philosophy

### Test-Driven Development
- Write tests before implementing features
- Maintain high test coverage (>90%)
- Use property-based testing for complex algorithms
- Test edge cases and error conditions

### Quality Assurance
- All tests must pass before merging
- Performance regression testing
- Compatibility testing across Python versions
- User experience testing with real projects

## Test Structure

### Test Organization
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Core analysis engine tests
│   │   ├── test_analyzers.py
│   │   ├── test_clone_detector.py
│   │   ├── test_fixture_extractor.py
│   │   └── test_scoring.py
│   ├── plugin/             # Plugin-specific tests
│   │   ├── test_hooks.py
│   │   ├── test_coverage.py
│   │   └── test_personas.py
│   └── cli/                # CLI tests
│       └── test_main.py
├── integration/            # Integration tests
│   ├── test_pytest_integration.py
│   ├── test_coverage_integration.py
│   └── test_ci_integration.py
├── performance/            # Performance and benchmark tests
│   ├── test_memory_usage.py
│   ├── test_analysis_speed.py
│   └── test_large_test_suites.py
├── fixtures/               # Test fixtures and sample data
│   ├── sample_tests/       # Sample test files with known issues
│   ├── expected_results/   # Expected analysis results
│   └── mock_data/          # Mock data for testing
└── e2e/                    # End-to-end tests
    ├── test_full_workflow.py
    ├── test_persona_switching.py
    └── test_ci_workflows.py
```

## Unit Testing

### Core Analysis Tests

#### AST Analyzer Tests
```python
import pytest
from pathlib import Path
from pytest_drill_sergeant.core.analyzers.ast_analyzer import ASTAnalyzer
from pytest_drill_sergeant.core.models import Finding, Severity

class TestASTAnalyzer:
    def test_private_access_detection(self):
        """Test detection of private attribute access"""
        analyzer = ASTAnalyzer()
        test_code = """
def test_something():
    obj = MyClass()
    result = obj._private_method()  # Should be detected
    assert result == expected
"""
        findings = analyzer.analyze_string(test_code)

        assert len(findings) == 1
        assert findings[0].rule_id == "private-access"
        assert findings[0].severity == Severity.WARN
        assert "_private_method" in findings[0].message

    def test_mock_overspecification_detection(self):
        """Test detection of excessive mock assertions"""
        analyzer = ASTAnalyzer()
        test_code = """
def test_something():
    mock_obj = Mock()
    mock_obj.method()
    mock_obj.assert_called_once()
    mock_obj.assert_called_with("arg")
    mock_obj.assert_has_calls([call.method("arg")])
    mock_obj.assert_any_call("arg")
"""
        findings = analyzer.analyze_string(test_code)

        assert len(findings) == 1
        assert findings[0].rule_id == "mock-overspec"
        assert findings[0].severity == Severity.WARN

    def test_structural_equality_detection(self):
        """Test detection of structural equality comparisons"""
        analyzer = ASTAnalyzer()
        test_code = """
def test_something():
    obj = MyClass()
    assert obj.__dict__ == expected_dict
    assert vars(obj) == expected_vars
    assert dataclasses.asdict(obj) == expected_asdict
"""
        findings = analyzer.analyze_string(test_code)

        assert len(findings) == 3
        assert all(f.rule_id == "structural-equality" for f in findings)
```

#### Clone Detector Tests
```python
import pytest
from pytest_drill_sergeant.core.analyzers.clone_detector import CloneDetector
from pytest_drill_sergeant.core.models import Cluster

class TestCloneDetector:
    def test_simhash_calculation(self):
        """Test SimHash calculation for AST similarity"""
        detector = CloneDetector()

        # Create two similar test functions
        test1 = """
def test_user_creation_alice():
    user = User("alice", "alice@example.com")
    assert user.name == "alice"
    assert user.email == "alice@example.com"
"""

        test2 = """
def test_user_creation_bob():
    user = User("bob", "bob@example.com")
    assert user.name == "bob"
    assert user.email == "bob@example.com"
"""

        hash1 = detector.compute_simhash(test1)
        hash2 = detector.compute_simhash(test2)

        # Should be similar (low Hamming distance)
        distance = detector.hamming_distance(hash1, hash2)
        assert distance <= 6  # Threshold

    def test_coverage_similarity(self):
        """Test coverage-based similarity detection"""
        detector = CloneDetector()

        # Mock coverage data
        coverage_data = {
            "test1": {1, 2, 3, 4, 5},
            "test2": {1, 2, 3, 4, 6},  # 80% overlap
            "test3": {10, 11, 12, 13, 14},  # No overlap
        }

        clusters = detector.find_dynamic_clones(coverage_data)

        # Should find cluster of test1 and test2
        assert len(clusters) == 1
        assert len(clusters[0].members) == 2
        assert "test1" in clusters[0].members
        assert "test2" in clusters[0].members
```

#### Scoring System Tests
```python
import pytest
from pytest_drill_sergeant.core.scoring.bis import calculate_bis
from pytest_drill_sergeant.core.models import TestFeatures

class TestBISScoring:
    def test_perfect_score(self):
        """Test perfect BIS score calculation"""
        features = TestFeatures(
            private_access_count=0,
            mock_assert_count=0,
            patched_internal_count=0,
            structural_compare_count=0,
            exception_message_length=0,
            public_api_assert_count=5
        )

        score = calculate_bis(features)
        assert score == 100.0

    def test_penalty_calculation(self):
        """Test BIS penalty calculation"""
        features = TestFeatures(
            private_access_count=2,  # -30 points
            mock_assert_count=3,     # -30 points
            patched_internal_count=1, # -15 points
            structural_compare_count=1, # -8 points
            exception_message_length=100, # -12 points (100/40 * 5)
            public_api_assert_count=2  # +16 points (min(2,5) * 8)
        )

        score = calculate_bis(features)
        expected = 100 - 30 - 30 - 15 - 8 - 12 + 16
        assert score == expected

    def test_score_bounds(self):
        """Test that BIS scores are bounded between 0 and 100"""
        features = TestFeatures(
            private_access_count=100,  # Massive penalty
            mock_assert_count=100,
            patched_internal_count=100,
            structural_compare_count=100,
            exception_message_length=10000,
            public_api_assert_count=0
        )

        score = calculate_bis(features)
        assert 0 <= score <= 100
```

### Persona System Tests
```python
import pytest
from pytest_drill_sergeant.plugin.personas import (
    DrillSergeantPersona,
    SnoopDoggPersona,
    MotivationalCoachPersona
)

class TestPersonas:
    def test_drill_sergeant_feedback(self):
        """Test drill sergeant persona feedback"""
        persona = DrillSergeantPersona()

        # Test pass feedback
        feedback = persona.on_test_pass("test_user_creation")
        assert "test_user_creation" in feedback
        assert any(word in feedback.upper() for word in ["OUTSTANDING", "GOOD", "FINALLY"])

        # Test fail feedback
        finding = Finding(
            rule_id="private-access",
            severity=Severity.WARN,
            path=Path("test.py"),
            location=(10, 5),
            message="Accessing private attribute"
        )
        feedback = persona.on_test_fail("test_user_creation", finding, None)
        assert "test_user_creation" in feedback
        assert any(word in feedback.upper() for word in ["AMATEUR", "PRIVATE", "MAGGOT"])

    def test_snoop_dogg_feedback(self):
        """Test Snoop Dogg persona feedback"""
        persona = SnoopDoggPersona()

        feedback = persona.on_test_pass("test_user_creation")
        assert "test_user_creation" in feedback
        assert any(word in feedback.lower() for word in ["homie", "dawg", "smooth"])

    def test_persona_consistency(self):
        """Test that personas provide consistent feedback"""
        personas = [
            DrillSergeantPersona(),
            SnoopDoggPersona(),
            MotivationalCoachPersona()
        ]

        for persona in personas:
            # All personas should mention the test name
            feedback = persona.on_test_pass("test_example")
            assert "test_example" in feedback

            # All personas should provide summary feedback
            metrics = RunMetrics(
                total_tests=100,
                aaa_rate=0.8,
                duplicate_tests=5,
                duplicate_clusters=2,
                param_rate=0.6,
                fixture_reuse_rate=0.7,
                non_determinism_rate=0.1,
                slow_tests_rate=0.2,
                style_smell_rate=0.05,
                bis_stats={},
                car_histogram={},
                clusters=[]
            )
            summary = persona.on_summary(metrics, None)
            assert len(summary) > 0
```

## Integration Testing

### Pytest Integration Tests
```python
import pytest
import subprocess
import tempfile
from pathlib import Path

class TestPytestIntegration:
    def test_plugin_installation(self):
        """Test that the plugin installs correctly"""
        result = subprocess.run(
            ["pytest", "--help"],
            capture_output=True,
            text=True
        )
        assert "drill-sergeant" in result.stdout

    def test_basic_analysis(self, tmp_path):
        """Test basic analysis functionality"""
        # Create a test file with known issues
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("""
def test_private_access():
    obj = MyClass()
    result = obj._private_method()  # Should be detected
    assert result == expected
""")

        # Run pytest with the plugin
        result = subprocess.run(
            ["pytest", str(test_file), "-v", "--ds-mode=advisory"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Check that analysis ran
        assert "drill-sergeant" in result.stdout.lower()
        assert result.returncode == 0

    def test_persona_switching(self, tmp_path):
        """Test switching between personas"""
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("""
def test_example():
    assert True
""")

        # Test drill sergeant persona
        result = subprocess.run(
            ["pytest", str(test_file), "--ds-persona=drill_sergeant"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        assert "drill" in result.stdout.lower() or "sergeant" in result.stdout.lower()

        # Test Snoop Dogg persona
        result = subprocess.run(
            ["pytest", str(test_file), "--ds-persona=snoop_dogg"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )
        assert any(word in result.stdout.lower() for word in ["homie", "dawg", "snoop"])
```

### Coverage Integration Tests
```python
import pytest
import coverage
from pytest_drill_sergeant.plugin.coverage import CoverageIntegration

class TestCoverageIntegration:
    def test_per_test_coverage_collection(self):
        """Test that coverage is collected per test"""
        integration = CoverageIntegration()

        # Mock test execution
        with integration.collect_coverage("test_example"):
            # Simulate test execution
            pass

        # Check that coverage data was collected
        assert integration.get_test_coverage("test_example") is not None

    def test_coverage_similarity_calculation(self):
        """Test coverage-based similarity calculation"""
        integration = CoverageIntegration()

        # Mock coverage data
        coverage_data = {
            "test1": {1, 2, 3, 4, 5},
            "test2": {1, 2, 3, 4, 6},
            "test3": {10, 11, 12, 13, 14},
        }

        similarity = integration.calculate_similarity("test1", "test2")
        assert similarity > 0.8  # High similarity

        similarity = integration.calculate_similarity("test1", "test3")
        assert similarity < 0.2  # Low similarity
```

## Performance Testing

### Memory Usage Tests
```python
import pytest
import psutil
import os
from pytest_drill_sergeant.core.analysis_pipeline import AnalysisPipeline

class TestMemoryUsage:
    def test_plugin_memory_usage(self):
        """Test that plugin doesn't use excessive memory"""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Initialize plugin
        pipeline = AnalysisPipeline()

        # Check memory usage
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory

        # Should not exceed 50MB
        assert memory_increase < 50 * 1024 * 1024

    def test_large_test_suite_handling(self):
        """Test handling of large test suites"""
        # Create a large number of test files
        test_files = []
        for i in range(1000):
            test_files.append(f"test_file_{i}.py")

        pipeline = AnalysisPipeline()

        # Should handle large test suites without memory issues
        results = pipeline.analyze_collection(test_files)
        assert len(results) == 1000
```

### Analysis Speed Tests
```python
import pytest
import time
from pytest_drill_sergeant.core.analyzers.ast_analyzer import ASTAnalyzer

class TestAnalysisSpeed:
    def test_ast_analysis_speed(self):
        """Test that AST analysis is fast enough"""
        analyzer = ASTAnalyzer()

        # Create a moderately complex test file
        test_code = """
def test_complex_functionality():
    # Arrange
    user = User("alice", "alice@example.com")
    order = Order(user, [Item("book", 10.99)])

    # Act
    result = process_order(order)

    # Assert
    assert result.status == "completed"
    assert result.total == 10.99
    assert result.user.email == "alice@example.com"
"""

        start_time = time.time()
        findings = analyzer.analyze_string(test_code)
        end_time = time.time()

        analysis_time = end_time - start_time

        # Should analyze in less than 100ms
        assert analysis_time < 0.1
        assert len(findings) >= 0  # Should complete successfully
```

## End-to-End Testing

### Full Workflow Tests
```python
import pytest
import subprocess
import tempfile
from pathlib import Path

class TestFullWorkflow:
    def test_complete_analysis_workflow(self, tmp_path):
        """Test complete analysis workflow from start to finish"""
        # Create a realistic test suite with various issues
        create_sample_test_suite(tmp_path)

        # Run complete analysis
        result = subprocess.run(
            ["pytest", "--ds-mode=advisory", "--ds-json-report=report.json"],
            cwd=tmp_path,
            capture_output=True,
            text=True
        )

        # Check that analysis completed
        assert result.returncode == 0

        # Check that JSON report was generated
        report_file = tmp_path / "report.json"
        assert report_file.exists()

        # Validate report content
        import json
        with open(report_file) as f:
            report = json.load(f)

        assert "metrics" in report
        assert "findings" in report
        assert "clusters" in report

    def test_ci_integration_workflow(self, tmp_path):
        """Test CI integration workflow"""
        # Create GitHub Actions workflow file
        workflow_file = tmp_path / ".github" / "workflows" / "test.yml"
        workflow_file.parent.mkdir(parents=True)
        workflow_file.write_text("""
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: pytest --ds-sarif-report=report.sarif
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: report.sarif
""")

        # Test that workflow would work (mock execution)
        assert workflow_file.exists()
```

## Quality Assurance

### Test Coverage Requirements
- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Critical Paths**: 100% coverage

### Performance Benchmarks
- **Plugin Startup**: <500ms
- **Per-Test Analysis**: <50ms
- **Memory Usage**: <200MB for 2000 tests
- **Large Test Suite**: <30 seconds for 1000 tests

### Compatibility Testing
- **Python Versions**: 3.10, 3.11, 3.12
- **Pytest Versions**: 8.0, 8.1, 8.2
- **Operating Systems**: Linux, macOS, Windows
- **CI Platforms**: GitHub Actions, GitLab CI, Jenkins

## Test Data Management

### Sample Test Files
```python
# tests/fixtures/sample_tests/test_with_issues.py
"""
Sample test file with various quality issues for testing
"""

def test_private_access():
    """Test that accesses private attributes - should be flagged"""
    obj = MyClass()
    result = obj._private_method()
    assert result == expected

def test_mock_overspecification():
    """Test with excessive mock assertions - should be flagged"""
    mock_obj = Mock()
    mock_obj.method()
    mock_obj.assert_called_once()
    mock_obj.assert_called_with("arg")
    mock_obj.assert_has_calls([call.method("arg")])

def test_structural_equality():
    """Test comparing internal structure - should be flagged"""
    obj = MyClass()
    assert obj.__dict__ == expected_dict
    assert vars(obj) == expected_vars

def test_missing_aaa_comments():
    """Test without AAA comments - should be flagged"""
    user = User("alice", "alice@example.com")
    result = user.validate()
    assert result is True

def test_good_behavior_focused_test():
    """Test that focuses on behavior - should score well"""
    # Arrange
    user = User("alice", "alice@example.com")

    # Act
    result = user.validate()

    # Assert
    assert result is True
    assert user.is_valid is True
```

### Expected Results
```python
# tests/fixtures/expected_results/test_with_issues_expected.json
{
  "findings": [
    {
      "rule_id": "private-access",
      "severity": "warn",
      "path": "test_with_issues.py",
      "location": [8, 12],
      "message": "Accessing private attribute: _private_method"
    },
    {
      "rule_id": "mock-overspec",
      "severity": "warn",
      "path": "test_with_issues.py",
      "location": [15, 5],
      "message": "Excessive mock assertions: 4"
    }
  ],
  "clusters": [],
  "bis_scores": {
    "test_private_access": 65.0,
    "test_mock_overspecification": 70.0,
    "test_good_behavior_focused_test": 95.0
  }
}
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
        pytest-version: [8.0, 8.1, 8.2]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install pytest==${{ matrix.pytest-version }}
          pip install -e .
          pip install -e .[dev]

      - name: Run unit tests
        run: pytest tests/unit -v --cov=pytest_drill_sergeant

      - name: Run integration tests
        run: pytest tests/integration -v

      - name: Run performance tests
        run: pytest tests/performance -v

      - name: Run end-to-end tests
        run: pytest tests/e2e -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Quality Gates
- All tests must pass
- Coverage must be >90%
- Performance benchmarks must be met
- No critical security vulnerabilities
- Documentation must be up to date
