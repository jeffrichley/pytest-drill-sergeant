"""File discovery and filtering system for pytest-drill-sergeant.

This module provides comprehensive file discovery and filtering capabilities
with support for include/exclude patterns, per-file ignores, and path-scoped
severity overrides.
"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .config_schema import DSConfig, SeverityLevel
from .rulespec import RuleRegistry


logger = logging.getLogger(__name__)


class FilePattern:
    """Represents a file pattern with its configuration."""
    
    def __init__(
        self,
        pattern: str,
        enabled: bool = True,
        severity_override: Optional[SeverityLevel] = None,
        ignored_rules: Optional[List[str]] = None,
    ):
        """Initialize file pattern.
        
        Args:
            pattern: Glob pattern for file matching
            enabled: Whether this pattern is enabled
            severity_override: Optional severity override for findings in matching files
            ignored_rules: List of rule codes to ignore for matching files
        """
        self.pattern = pattern
        self.enabled = enabled
        self.severity_override = severity_override
        self.ignored_rules = ignored_rules or []
    
    def matches(self, file_path: Path, project_root: Path) -> bool:
        """Check if this pattern matches the given file path.
        
        Args:
            file_path: Path to check
            project_root: Project root directory
            
        Returns:
            True if the pattern matches the file
        """
        if not self.enabled:
            return False
            
        try:
            # Convert to relative path for pattern matching
            rel_path = file_path.relative_to(project_root)
            
            # Use glob pattern matching
            path_str = str(rel_path).replace("\\", "/")
            
            # Use glob.glob to test if the pattern matches
            import glob
            # Create a temporary path to test against
            test_path = project_root / self.pattern
            # Use glob to find matching files
            matching_files = list(project_root.glob(self.pattern))
            # Check if our file is in the matching files
            return file_path in matching_files
        except ValueError:
            # File is not under project root
            return False
    
    def __repr__(self) -> str:
        return f"FilePattern(pattern='{self.pattern}', enabled={self.enabled})"


class FileDiscoveryConfig:
    """Configuration for file discovery and filtering."""
    
    def __init__(self, config: DSConfig):
        """Initialize file discovery configuration.
        
        Args:
            config: Main configuration object
        """
        self.config = config
        self.project_root = config.project_root or Path.cwd()
        
        # Build include patterns from test_patterns and include_patterns
        all_include_patterns = config.test_patterns + config.include_patterns
        self.include_patterns = [
            FilePattern(pattern, enabled=True)
            for pattern in all_include_patterns
        ]
        
        # Build exclude patterns from ignore_patterns and exclude_patterns
        all_exclude_patterns = config.ignore_patterns + config.exclude_patterns
        self.exclude_patterns = [
            FilePattern(pattern, enabled=True)
            for pattern in all_exclude_patterns
        ]
        
        # Build per-file ignore patterns
        self.per_file_ignores = {}
        for pattern, rule_codes in config.per_file_ignores.items():
            self.per_file_ignores[pattern] = FilePattern(
                pattern=pattern,
                enabled=True,
                ignored_rules=rule_codes
            )
        
        # Build per-file severity overrides
        self.per_file_severity_overrides = {}
        for pattern, severity in config.per_file_severity_overrides.items():
            self.per_file_severity_overrides[pattern] = FilePattern(
                pattern=pattern,
                enabled=True,
                severity_override=severity
            )
        
        # Build per-file rule overrides
        self.per_file_rule_overrides = {}
        for pattern, rule_configs in config.per_file_rule_overrides.items():
            self.per_file_rule_overrides[pattern] = FilePattern(
                pattern=pattern,
                enabled=True,
                ignored_rules=list(rule_configs.keys())  # Store rule codes for matching
            )
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be analyzed
        """
        # Check if file is under project root
        try:
            file_path.relative_to(self.project_root)
        except ValueError:
            return False
        
        # Check if file matches any include pattern
        matches_include = any(
            pattern.matches(file_path, self.project_root)
            for pattern in self.include_patterns
        )
        
        if not matches_include:
            return False
        
        # Check if file matches any exclude pattern
        matches_exclude = any(
            pattern.matches(file_path, self.project_root)
            for pattern in self.exclude_patterns
        )
        
        return not matches_exclude
    
    def get_ignored_rules(self, file_path: Path) -> List[str]:
        """Get list of rules to ignore for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of rule codes to ignore
        """
        ignored_rules = []
        
        # Check per-file ignores
        for pattern in self.per_file_ignores.values():
            if pattern.matches(file_path, self.project_root):
                ignored_rules.extend(pattern.ignored_rules)
        
        return list(set(ignored_rules))  # Remove duplicates
    
    def get_severity_override(self, file_path: Path) -> Optional[SeverityLevel]:
        """Get severity override for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Severity override if any, None otherwise
        """
        # Check per-file severity overrides
        for pattern in self.per_file_severity_overrides.values():
            if pattern.matches(file_path, self.project_root):
                return pattern.severity_override
        
        return None
    
    def get_rule_overrides(self, file_path: Path) -> Dict[str, RuleConfig]:
        """Get rule configuration overrides for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary of rule codes to their overridden configurations
        """
        rule_overrides = {}
        
        # Check per-file rule overrides
        for pattern in self.per_file_rule_overrides.values():
            if pattern.matches(file_path, self.project_root):
                # Get the original rule configs for this pattern
                pattern_key = pattern.pattern
                if pattern_key in self.config.per_file_rule_overrides:
                    rule_overrides.update(self.config.per_file_rule_overrides[pattern_key])
        
        return rule_overrides
    
    def get_matching_patterns(self, file_path: Path) -> List[FilePattern]:
        """Get all patterns that match a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of matching patterns
        """
        matching_patterns = []
        
        # Check include patterns
        for pattern in self.include_patterns:
            if pattern.matches(file_path, self.project_root):
                matching_patterns.append(pattern)
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.matches(file_path, self.project_root):
                matching_patterns.append(pattern)
        
        # Check per-file ignore patterns
        for pattern in self.per_file_ignores.values():
            if pattern.matches(file_path, self.project_root):
                matching_patterns.append(pattern)
        
        # Check per-file severity override patterns
        for pattern in self.per_file_severity_overrides.values():
            if pattern.matches(file_path, self.project_root):
                matching_patterns.append(pattern)
        
        # Check per-file rule override patterns
        for pattern in self.per_file_rule_overrides.values():
            if pattern.matches(file_path, self.project_root):
                matching_patterns.append(pattern)
        
        return matching_patterns


class FileDiscovery:
    """Main file discovery and filtering system."""
    
    def __init__(self, config: DSConfig):
        """Initialize file discovery.
        
        Args:
            config: Main configuration object
        """
        self.config = config
        self.discovery_config = FileDiscoveryConfig(config)
        self._discovered_files: Optional[Set[Path]] = None
        self._file_cache: Dict[Path, Dict] = {}
    
    def discover_files(self, force_refresh: bool = False) -> Set[Path]:
        """Discover all files that should be analyzed.
        
        Args:
            force_refresh: Force refresh of discovered files
            
        Returns:
            Set of file paths to analyze
        """
        if self._discovered_files is not None and not force_refresh:
            return self._discovered_files.copy()
        
        discovered_files = set()
        project_root = self.discovery_config.project_root
        
        # Walk through project directory
        for file_path in project_root.rglob("*.py"):
            if self.discovery_config.should_analyze_file(file_path):
                discovered_files.add(file_path)
        
        self._discovered_files = discovered_files
        logger.info("Discovered %d files for analysis", len(discovered_files))
        
        return discovered_files.copy()
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be analyzed
        """
        return self.discovery_config.should_analyze_file(file_path)
    
    def get_file_config(self, file_path: Path) -> Dict:
        """Get configuration for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file-specific configuration
        """
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        config = {
            "ignored_rules": self.discovery_config.get_ignored_rules(file_path),
            "severity_override": self.discovery_config.get_severity_override(file_path),
            "rule_overrides": self.discovery_config.get_rule_overrides(file_path),
            "matching_patterns": [
                pattern.pattern for pattern in self.discovery_config.get_matching_patterns(file_path)
            ],
            "should_analyze": self.should_analyze_file(file_path),
        }
        
        self._file_cache[file_path] = config
        return config
    
    def is_rule_ignored_for_file(self, file_path: Path, rule_code: str) -> bool:
        """Check if a rule is ignored for a specific file.
        
        Args:
            file_path: Path to the file
            rule_code: Rule code to check
            
        Returns:
            True if the rule is ignored for this file
        """
        file_config = self.get_file_config(file_path)
        return rule_code in file_config["ignored_rules"]
    
    def get_effective_severity(self, file_path: Path, rule_code: str, default_severity: SeverityLevel) -> SeverityLevel:
        """Get the effective severity for a rule in a specific file.
        
        Args:
            file_path: Path to the file
            rule_code: Rule code
            default_severity: Default severity for the rule
            
        Returns:
            Effective severity level
        """
        file_config = self.get_file_config(file_path)
        
        # Check for file-specific rule override first
        if rule_code in file_config["rule_overrides"]:
            rule_override = file_config["rule_overrides"][rule_code]
            if rule_override.severity:
                return rule_override.severity
        
        # Check for file-specific severity override
        if file_config["severity_override"]:
            return file_config["severity_override"]
        
        # Check for rule-specific severity override in config
        if rule_code in self.config.rules:
            rule_config = self.config.rules[rule_code]
            if rule_config.severity:
                return rule_config.severity
        
        return default_severity
    
    def get_effective_rule_config(self, file_path: Path, rule_code: str) -> Optional[RuleConfig]:
        """Get the effective rule configuration for a specific file.
        
        Args:
            file_path: Path to the file
            rule_code: Rule code
            
        Returns:
            Effective rule configuration or None if not found
        """
        file_config = self.get_file_config(file_path)
        
        # Check for file-specific rule override first
        if rule_code in file_config["rule_overrides"]:
            return file_config["rule_overrides"][rule_code]
        
        # Fall back to global rule config
        if rule_code in self.config.rules:
            return self.config.rules[rule_code]
        
        return None
    
    def get_analysis_files(self, paths: Optional[List[Union[str, Path]]] = None) -> List[Path]:
        """Get list of files to analyze, optionally filtered by provided paths.
        
        Args:
            paths: Optional list of paths to filter by
            
        Returns:
            List of file paths to analyze
        """
        if paths is None:
            return list(self.discover_files())
        
        analysis_files = []
        project_root = self.discovery_config.project_root
        
        for path in paths:
            path_obj = Path(path)
            
            if not path_obj.is_absolute():
                path_obj = project_root / path_obj
            
            if path_obj.is_file():
                # Single file
                if self.should_analyze_file(path_obj):
                    analysis_files.append(path_obj)
            elif path_obj.is_dir():
                # Directory - find all matching files
                for file_path in path_obj.rglob("*.py"):
                    if self.should_analyze_file(file_path):
                        analysis_files.append(file_path)
            else:
                # Pattern - use glob matching
                for file_path in project_root.glob(str(path_obj)):
                    if file_path.is_file() and self.should_analyze_file(file_path):
                        analysis_files.append(file_path)
        
        return sorted(set(analysis_files))
    
    def clear_cache(self) -> None:
        """Clear the file discovery cache."""
        self._discovered_files = None
        self._file_cache.clear()
    
    def get_discovery_stats(self) -> Dict:
        """Get statistics about file discovery.
        
        Returns:
            Dictionary with discovery statistics
        """
        discovered_files = self.discover_files()
        
        stats = {
            "total_files": len(discovered_files),
            "include_patterns": len(self.discovery_config.include_patterns),
            "exclude_patterns": len(self.discovery_config.exclude_patterns),
            "per_file_ignores": len(self.discovery_config.per_file_ignores),
            "per_file_severity_overrides": len(self.discovery_config.per_file_severity_overrides),
            "per_file_rule_overrides": len(self.discovery_config.per_file_rule_overrides),
            "project_root": str(self.discovery_config.project_root),
        }
        
        # Count files by pattern
        pattern_counts = {}
        for file_path in discovered_files:
            matching_patterns = self.discovery_config.get_matching_patterns(file_path)
            for pattern in matching_patterns:
                pattern_counts[pattern.pattern] = pattern_counts.get(pattern.pattern, 0) + 1
        
        stats["pattern_counts"] = pattern_counts
        
        return stats


def create_file_discovery(config: DSConfig) -> FileDiscovery:
    """Create a file discovery instance from configuration.
    
    Args:
        config: Main configuration object
        
    Returns:
        FileDiscovery instance
    """
    return FileDiscovery(config)


def validate_file_patterns(config: DSConfig) -> List[str]:
    """Validate file patterns in configuration.
    
    Args:
        config: Main configuration object
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Validate test patterns
    for pattern in config.test_patterns:
        if not pattern.strip():
            errors.append("Test patterns cannot be empty")
        elif not _is_valid_glob_pattern(pattern):
            errors.append(f"Invalid glob pattern in test_patterns: '{pattern}'")
    
    # Validate ignore patterns
    for pattern in config.ignore_patterns:
        if not pattern.strip():
            errors.append("Ignore patterns cannot be empty")
        elif not _is_valid_glob_pattern(pattern):
            errors.append(f"Invalid glob pattern in ignore_patterns: '{pattern}'")
    
    # Validate per-file ignore patterns
    for pattern, rule_codes in config.per_file_ignores.items():
        if not pattern.strip():
            errors.append("Per-file ignore patterns cannot be empty")
        elif not _is_valid_glob_pattern(pattern):
            errors.append(f"Invalid glob pattern in per_file_ignores: '{pattern}'")
        
        # Validate rule codes
        for rule_code in rule_codes:
            if not RuleRegistry.is_valid_rule(rule_code):
                errors.append(f"Invalid rule code in per_file_ignores: '{rule_code}'")
    
    return errors


def _is_valid_glob_pattern(pattern: str) -> bool:
    """Check if a pattern is a valid glob pattern.
    
    Args:
        pattern: Pattern to validate
        
    Returns:
        True if the pattern is valid
    """
    try:
        # Test the pattern with a dummy path
        fnmatch.fnmatch("test_file.py", pattern)
        return True
    except Exception:
        return False
