"""Tests for file discovery and filtering system."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from pytest_drill_sergeant.core.config_schema import DSConfig, SeverityLevel, RuleConfig, create_default_config
from pytest_drill_sergeant.core.file_discovery import (
    FilePattern,
    FileDiscoveryConfig,
    FileDiscovery,
    create_file_discovery,
    validate_file_patterns,
)


def create_test_config(project_root, **overrides):
    """Create a test configuration with the given overrides."""
    config = create_default_config()
    config.project_root = project_root
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


class TestFilePattern:
    """Test FilePattern class."""
    
    def test_file_pattern_creation(self):
        """Test FilePattern creation."""
        pattern = FilePattern("test_*.py", enabled=True)
        assert pattern.pattern == "test_*.py"
        assert pattern.enabled is True
        assert pattern.severity_override is None
        assert pattern.ignored_rules == []
    
    def test_file_pattern_with_options(self):
        """Test FilePattern with all options."""
        pattern = FilePattern(
            "test_*.py",
            enabled=True,
            severity_override=SeverityLevel.ERROR,
            ignored_rules=["DS201", "DS202"]
        )
        assert pattern.pattern == "test_*.py"
        assert pattern.enabled is True
        assert pattern.severity_override == SeverityLevel.ERROR
        assert pattern.ignored_rules == ["DS201", "DS202"]
    
    def test_file_pattern_matches(self, tmp_path):
        """Test file pattern matching."""
        project_root = tmp_path
        test_file = project_root / "test_example.py"
        test_file.write_text("")
        
        pattern = FilePattern("test_*.py")
        assert pattern.matches(test_file, project_root) is True
        
        # Test non-matching file
        other_file = project_root / "example.py"
        other_file.write_text("")
        assert pattern.matches(other_file, project_root) is False
    
    def test_file_pattern_disabled(self, tmp_path):
        """Test disabled file pattern."""
        project_root = tmp_path
        test_file = project_root / "test_example.py"
        test_file.write_text("")
        
        pattern = FilePattern("test_*.py", enabled=False)
        assert pattern.matches(test_file, project_root) is False
    
    def test_file_pattern_outside_project_root(self, tmp_path):
        """Test file pattern with file outside project root."""
        project_root = tmp_path
        outside_file = tmp_path.parent / "test_example.py"
        outside_file.write_text("")
        
        pattern = FilePattern("test_*.py")
        assert pattern.matches(outside_file, project_root) is False


class TestFileDiscoveryConfig:
    """Test FileDiscoveryConfig class."""
    
    def test_config_creation(self, tmp_path):
        """Test FileDiscoveryConfig creation."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
            per_file_ignores={"test_legacy.py": ["DS201"]},
            include_patterns=["tests/**/*.py"],
            exclude_patterns=["**/migrations/*.py"],
            per_file_severity_overrides={"test_critical.py": SeverityLevel.ERROR},
            per_file_rule_overrides={"test_special.py": {"DS201": RuleConfig(enabled=False)}},
        )
        
        discovery_config = FileDiscoveryConfig(config)
        
        assert len(discovery_config.include_patterns) == 2  # test_patterns + include_patterns
        assert len(discovery_config.exclude_patterns) == 2  # ignore_patterns + exclude_patterns
        assert len(discovery_config.per_file_ignores) == 1
        assert len(discovery_config.per_file_severity_overrides) == 1
        assert len(discovery_config.per_file_rule_overrides) == 1
    
    def test_should_analyze_file(self, tmp_path):
        """Test should_analyze_file method."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
        )
        
        discovery_config = FileDiscoveryConfig(config)
        
        # Create test files
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        
        integration_file = tmp_path / "test_integration.py"
        integration_file.write_text("")
        
        other_file = tmp_path / "example.py"
        other_file.write_text("")
        
        assert discovery_config.should_analyze_file(test_file) is True
        assert discovery_config.should_analyze_file(integration_file) is False
        assert discovery_config.should_analyze_file(other_file) is False
    
    def test_get_ignored_rules(self, tmp_path):
        """Test get_ignored_rules method."""
        config = create_test_config(
            tmp_path,
            
            per_file_ignores={
                "test_legacy.py": ["DS201", "DS202"],
                "test_old.py": ["DS301"],
            },
        )
        
        discovery_config = FileDiscoveryConfig(config)
        
        # Create test files
        legacy_file = tmp_path / "test_legacy.py"
        legacy_file.write_text("")
        
        old_file = tmp_path / "test_old.py"
        old_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        assert set(discovery_config.get_ignored_rules(legacy_file)) == {"DS201", "DS202"}
        assert set(discovery_config.get_ignored_rules(old_file)) == {"DS301"}
        assert discovery_config.get_ignored_rules(normal_file) == []
    
    def test_get_severity_override(self, tmp_path):
        """Test get_severity_override method."""
        config = create_test_config(
            tmp_path,
            
            per_file_severity_overrides={
                "test_critical.py": SeverityLevel.ERROR,
                "test_warning.py": SeverityLevel.WARNING,
            },
        )
        
        discovery_config = FileDiscoveryConfig(config)
        
        # Create test files
        critical_file = tmp_path / "test_critical.py"
        critical_file.write_text("")
        
        warning_file = tmp_path / "test_warning.py"
        warning_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        assert discovery_config.get_severity_override(critical_file) == SeverityLevel.ERROR
        assert discovery_config.get_severity_override(warning_file) == SeverityLevel.WARNING
        assert discovery_config.get_severity_override(normal_file) is None
    
    def test_get_rule_overrides(self, tmp_path):
        """Test get_rule_overrides method."""
        config = create_test_config(
            tmp_path,
            
            per_file_rule_overrides={
                "test_special.py": {
                    "DS201": RuleConfig(enabled=False, severity=SeverityLevel.INFO),
                    "DS202": RuleConfig(threshold=0.5),
                }
            },
        )
        
        discovery_config = FileDiscoveryConfig(config)
        
        # Create test file
        special_file = tmp_path / "test_special.py"
        special_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        overrides = discovery_config.get_rule_overrides(special_file)
        assert "DS201" in overrides
        assert "DS202" in overrides
        assert overrides["DS201"].enabled is False
        assert overrides["DS201"].severity == SeverityLevel.INFO
        assert overrides["DS202"].threshold == 0.5
        
        assert discovery_config.get_rule_overrides(normal_file) == {}


class TestFileDiscovery:
    """Test FileDiscovery class."""
    
    def test_discovery_creation(self, tmp_path):
        """Test FileDiscovery creation."""
        config = create_test_config(tmp_path)
        discovery = FileDiscovery(config)
        
        assert discovery.config == config
        assert discovery.discovery_config.project_root == tmp_path
        assert discovery._discovered_files is None
    
    def test_discover_files(self, tmp_path):
        """Test discover_files method."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        test_file1 = tmp_path / "test_example1.py"
        test_file1.write_text("")
        
        test_file2 = tmp_path / "test_example2.py"
        test_file2.write_text("")
        
        integration_file = tmp_path / "test_integration.py"
        integration_file.write_text("")
        
        other_file = tmp_path / "example.py"
        other_file.write_text("")
        
        discovered_files = discovery.discover_files()
        
        assert test_file1 in discovered_files
        assert test_file2 in discovered_files
        assert integration_file not in discovered_files
        assert other_file not in discovered_files
    
    def test_should_analyze_file(self, tmp_path):
        """Test should_analyze_file method."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        
        integration_file = tmp_path / "test_integration.py"
        integration_file.write_text("")
        
        assert discovery.should_analyze_file(test_file) is True
        assert discovery.should_analyze_file(integration_file) is False
    
    def test_get_file_config(self, tmp_path):
        """Test get_file_config method."""
        config = create_test_config(
            tmp_path,
            
            per_file_ignores={"test_legacy.py": ["DS201"]},
            per_file_severity_overrides={"test_critical.py": SeverityLevel.ERROR},
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        legacy_file = tmp_path / "test_legacy.py"
        legacy_file.write_text("")
        
        critical_file = tmp_path / "test_critical.py"
        critical_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        # Test legacy file config
        legacy_config = discovery.get_file_config(legacy_file)
        assert "DS201" in legacy_config["ignored_rules"]
        assert legacy_config["severity_override"] is None
        assert legacy_config["should_analyze"] is True
        
        # Test critical file config
        critical_config = discovery.get_file_config(critical_file)
        assert critical_config["ignored_rules"] == []
        assert critical_config["severity_override"] == SeverityLevel.ERROR
        assert critical_config["should_analyze"] is True
        
        # Test normal file config
        normal_config = discovery.get_file_config(normal_file)
        assert normal_config["ignored_rules"] == []
        assert normal_config["severity_override"] is None
        assert normal_config["should_analyze"] is True
    
    def test_is_rule_ignored_for_file(self, tmp_path):
        """Test is_rule_ignored_for_file method."""
        config = create_test_config(
            tmp_path,
            
            per_file_ignores={"test_legacy.py": ["DS201", "DS202"]},
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        legacy_file = tmp_path / "test_legacy.py"
        legacy_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        assert discovery.is_rule_ignored_for_file(legacy_file, "DS201") is True
        assert discovery.is_rule_ignored_for_file(legacy_file, "DS202") is True
        assert discovery.is_rule_ignored_for_file(legacy_file, "DS301") is False
        
        assert discovery.is_rule_ignored_for_file(normal_file, "DS201") is False
    
    def test_get_effective_severity(self, tmp_path):
        """Test get_effective_severity method."""
        config = create_test_config(
            tmp_path,
            
            per_file_severity_overrides={"test_critical.py": SeverityLevel.ERROR},
            per_file_rule_overrides={
                "test_special.py": {"DS201": RuleConfig(severity=SeverityLevel.INFO)}
            },
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        critical_file = tmp_path / "test_critical.py"
        critical_file.write_text("")
        
        special_file = tmp_path / "test_special.py"
        special_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        # Test critical file (file-level severity override)
        assert discovery.get_effective_severity(critical_file, "DS201", SeverityLevel.WARNING) == SeverityLevel.ERROR
        
        # Test special file (rule-level override)
        assert discovery.get_effective_severity(special_file, "DS201", SeverityLevel.WARNING) == SeverityLevel.INFO
        
        # Test normal file (default severity)
        assert discovery.get_effective_severity(normal_file, "DS201", SeverityLevel.WARNING) == SeverityLevel.WARNING
    
    def test_get_effective_rule_config(self, tmp_path):
        """Test get_effective_rule_config method."""
        config = create_test_config(
            tmp_path,
            
            rules={"DS201": RuleConfig(enabled=True, severity=SeverityLevel.WARNING)},
            per_file_rule_overrides={
                "test_special.py": {"DS201": RuleConfig(enabled=False, severity=SeverityLevel.INFO)}
            },
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        special_file = tmp_path / "test_special.py"
        special_file.write_text("")
        
        normal_file = tmp_path / "test_normal.py"
        normal_file.write_text("")
        
        # Test special file (file-level rule override)
        special_config = discovery.get_effective_rule_config(special_file, "DS201")
        assert special_config is not None
        assert special_config.enabled is False
        assert special_config.severity == SeverityLevel.INFO
        
        # Test normal file (global rule config)
        normal_config = discovery.get_effective_rule_config(normal_file, "DS201")
        assert normal_config is not None
        assert normal_config.enabled is True
        assert normal_config.severity == SeverityLevel.WARNING
        
        # Test non-existent rule
        assert discovery.get_effective_rule_config(normal_file, "DS999") is None
    
    def test_get_analysis_files(self, tmp_path):
        """Test get_analysis_files method."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        test_file1 = tmp_path / "test_example1.py"
        test_file1.write_text("")
        
        test_file2 = tmp_path / "test_example2.py"
        test_file2.write_text("")
        
        integration_file = tmp_path / "test_integration.py"
        integration_file.write_text("")
        
        other_file = tmp_path / "example.py"
        other_file.write_text("")
        
        # Test with no paths (discover all)
        all_files = discovery.get_analysis_files()
        assert test_file1 in all_files
        assert test_file2 in all_files
        assert integration_file not in all_files
        assert other_file not in all_files
        
        # Test with specific file
        specific_files = discovery.get_analysis_files([str(test_file1)])
        assert specific_files == [test_file1]
        
        # Test with directory
        dir_files = discovery.get_analysis_files([str(tmp_path)])
        assert test_file1 in dir_files
        assert test_file2 in dir_files
        assert integration_file not in dir_files
        assert other_file not in dir_files
    
    def test_clear_cache(self, tmp_path):
        """Test clear_cache method."""
        config = create_test_config(tmp_path)
        discovery = FileDiscovery(config)
        
        # Discover files to populate cache
        discovery.discover_files()
        
        # Add some file configs to cache
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        discovery.get_file_config(test_file)
        
        # Verify cache is populated
        assert discovery._discovered_files is not None
        assert len(discovery._file_cache) > 0
        
        # Clear cache
        discovery.clear_cache()
        
        # Verify cache is cleared
        assert discovery._discovered_files is None
        assert len(discovery._file_cache) == 0
    
    def test_get_discovery_stats(self, tmp_path):
        """Test get_discovery_stats method."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            ignore_patterns=["*_integration.py"],
            per_file_ignores={"test_legacy.py": ["DS201"]},
            per_file_severity_overrides={"test_critical.py": SeverityLevel.ERROR},
            per_file_rule_overrides={"test_special.py": {"DS201": RuleConfig(enabled=False)}},
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        
        stats = discovery.get_discovery_stats()
        
        assert stats["total_files"] == 1
        assert stats["include_patterns"] == 1  # test_patterns
        assert stats["exclude_patterns"] == 1  # ignore_patterns
        assert stats["per_file_ignores"] == 1
        assert stats["per_file_severity_overrides"] == 1
        assert stats["per_file_rule_overrides"] == 1
        assert stats["project_root"] == str(tmp_path)
        assert "pattern_counts" in stats


class TestFileDiscoveryIntegration:
    """Test file discovery integration functions."""
    
    def test_create_file_discovery(self, tmp_path):
        """Test create_file_discovery function."""
        config = create_test_config(tmp_path)
        discovery = create_file_discovery(config)
        
        assert isinstance(discovery, FileDiscovery)
        assert discovery.config == config
    
    def test_validate_file_patterns_valid(self, tmp_path):
        """Test validate_file_patterns with valid patterns."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py", "tests/**/*.py"],
            ignore_patterns=["*_integration.py", "**/migrations/*.py"],
            per_file_ignores={"test_legacy.py": ["DS201"]},
        )
        
        errors = validate_file_patterns(config)
        assert errors == []
    
    def test_validate_file_patterns_invalid(self, tmp_path):
        """Test validate_file_patterns with invalid patterns."""
        # Create a mock config object with invalid patterns
        class MockConfig:
            def __init__(self):
                self.test_patterns = ["", "test_*.py"]  # Empty pattern
                self.ignore_patterns = ["invalid[pattern"]  # Invalid glob pattern
                self.per_file_ignores = {"test_legacy.py": ["INVALID"]}  # Invalid rule code
        
        config = MockConfig()
        errors = validate_file_patterns(config)
        assert len(errors) > 0
        assert any("cannot be empty" in error for error in errors)
        assert any("Invalid rule code" in error for error in errors)
    
    def test_complex_file_discovery_scenario(self, tmp_path):
        """Test complex file discovery scenario with multiple patterns."""
        config = create_test_config(
            tmp_path,
            
            test_patterns=["test_*.py"],
            include_patterns=["tests/**/*.py", "specs/**/*.py"],
            ignore_patterns=["*_integration.py"],
            exclude_patterns=["**/migrations/*.py", "**/legacy/*.py"],
            per_file_ignores={
                "test_legacy.py": ["DS201", "DS202"],
                "test_old.py": ["DS301"],
            },
            per_file_severity_overrides={
                "test_critical.py": SeverityLevel.ERROR,
                "test_warning.py": SeverityLevel.WARNING,
            },
            per_file_rule_overrides={
                "test_special.py": {
                    "DS201": RuleConfig(enabled=False, severity=SeverityLevel.INFO),
                    "DS202": RuleConfig(threshold=0.5),
                }
            },
        )
        
        discovery = FileDiscovery(config)
        
        # Create test files
        test_files = [
            "test_example.py",
            "test_integration.py",  # Should be excluded
            "test_legacy.py",
            "test_old.py",
            "test_critical.py",
            "test_warning.py",
            "test_special.py",
            "example.py",  # Should be excluded
        ]
        
        for filename in test_files:
            file_path = tmp_path / filename
            file_path.write_text("")
        
        # Create subdirectories
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_subdir.py").write_text("")
        
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()
        (specs_dir / "test_spec.py").write_text("")
        
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "test_migration.py").write_text("")
        
        legacy_dir = tmp_path / "legacy"
        legacy_dir.mkdir()
        (legacy_dir / "test_legacy_file.py").write_text("")
        
        # Discover files
        discovered_files = discovery.discover_files()
        
        # Check that correct files are discovered
        expected_files = {
            tmp_path / "test_example.py",
            tmp_path / "test_legacy.py",
            tmp_path / "test_old.py",
            tmp_path / "test_critical.py",
            tmp_path / "test_warning.py",
            tmp_path / "test_special.py",
            tests_dir / "test_subdir.py",
            specs_dir / "test_spec.py",
        }
        
        assert set(discovered_files) == expected_files
        
        # Test file-specific configurations
        legacy_file = tmp_path / "test_legacy.py"
        legacy_config = discovery.get_file_config(legacy_file)
        assert set(legacy_config["ignored_rules"]) == {"DS201", "DS202"}
        
        critical_file = tmp_path / "test_critical.py"
        critical_config = discovery.get_file_config(critical_file)
        assert critical_config["severity_override"] == SeverityLevel.ERROR
        
        special_file = tmp_path / "test_special.py"
        special_config = discovery.get_file_config(special_file)
        assert "DS201" in special_config["rule_overrides"]
        assert "DS202" in special_config["rule_overrides"]
        
        # Test effective configurations
        assert discovery.get_effective_severity(special_file, "DS201", SeverityLevel.WARNING) == SeverityLevel.INFO
        assert discovery.get_effective_severity(critical_file, "DS201", SeverityLevel.WARNING) == SeverityLevel.ERROR
        
        special_rule_config = discovery.get_effective_rule_config(special_file, "DS201")
        assert special_rule_config is not None
        assert special_rule_config.enabled is False
        assert special_rule_config.severity == SeverityLevel.INFO
