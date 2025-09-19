"""Strict configuration schema for pytest-drill-sergeant.

This module provides versioned, strictly validated configuration schemas
with helpful error messages and unknown key detection.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)


class SchemaVersion(str, Enum):
    """Configuration schema versions."""
    V1_0 = "1.0"


class SeverityLevel(str, Enum):
    """Severity levels for findings."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class Profile(str, Enum):
    """Configuration profiles."""
    STANDARD = "standard"
    STRICT = "strict"
    RELAXED = "relaxed"


class OutputFormat(str, Enum):
    """Output format options."""
    TERMINAL = "terminal"
    JSON = "json"
    SARIF = "sarif"


class RuleConfig(BaseModel):
    """Configuration for a specific rule."""
    
    model_config = ConfigDict(extra="forbid")
    
    enabled: bool = Field(True, description="Whether the rule is enabled")
    severity: Optional[SeverityLevel] = Field(None, description="Override severity level")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Rule-specific threshold")
    tags: List[str] = Field(default_factory=list, description="Rule-specific tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific metadata")
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags are non-empty strings."""
        for tag in v:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("Tags must be non-empty strings")
        return v


class ProfileConfig(BaseModel):
    """Configuration for a specific profile."""
    
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    rules: Dict[str, RuleConfig] = Field(default_factory=dict, description="Rule configurations")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Profile thresholds")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Profile-specific settings")
    
    @field_validator("rules")
    @classmethod
    def validate_rule_codes(cls, v: Dict[str, RuleConfig]) -> Dict[str, RuleConfig]:
        """Validate that rule keys are valid rule codes."""
        from pytest_drill_sergeant.core.rulespec import RuleRegistry
        
        for rule_code in v.keys():
            if not RuleRegistry.is_valid_rule(rule_code):
                # Provide helpful suggestions for invalid rule codes
                suggestions = _suggest_rule_codes(rule_code)
                if suggestions:
                    raise ValueError(
                        f"Invalid rule code '{rule_code}'. "
                        f"Did you mean: {', '.join(suggestions)}?"
                    )
                else:
                    raise ValueError(f"Invalid rule code '{rule_code}'. Use 'DS###' format.")
        return v


class OutputConfig(BaseModel):
    """Output configuration."""
    
    model_config = ConfigDict(extra="forbid")
    
    format: OutputFormat = Field(OutputFormat.TERMINAL, description="Output format")
    json_path: Optional[Path] = Field(None, description="Path for JSON output")
    sarif_path: Optional[Path] = Field(None, description="Path for SARIF output")
    verbose: bool = Field(False, description="Enable verbose output")
    color: bool = Field(True, description="Enable colored output")
    show_source: bool = Field(True, description="Show source code snippets")
    show_suggestions: bool = Field(True, description="Show fix suggestions")


class AnalysisConfig(BaseModel):
    """Analysis configuration."""
    
    model_config = ConfigDict(extra="forbid")
    
    parallel: bool = Field(True, description="Enable parallel analysis")
    max_workers: int = Field(4, ge=1, le=32, description="Maximum worker processes")
    cache_ast: bool = Field(True, description="Cache AST parsing")
    timeout: Optional[float] = Field(None, ge=1.0, description="Analysis timeout in seconds")
    memory_limit: Optional[int] = Field(None, ge=100, description="Memory limit in MB")


class DSConfig(BaseModel):
    """Main configuration schema for pytest-drill-sergeant."""
    
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    
    # Schema version - required for future compatibility
    schema_version: SchemaVersion = Field(
        SchemaVersion.V1_0, 
        description="Configuration schema version"
    )
    
    # Core settings
    profile: Profile = Field(Profile.STANDARD, description="Active configuration profile")
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict, description="Available profiles")
    
    # Analysis settings
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig, description="Analysis configuration")
    
    # Output settings
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output configuration")
    
    # Global rule settings
    rules: Dict[str, RuleConfig] = Field(default_factory=dict, description="Global rule configurations")
    
    # Thresholds
    bis_threshold: float = Field(70.0, ge=0.0, le=100.0, description="BIS threshold")
    brs_threshold: float = Field(60.0, ge=0.0, le=100.0, description="BRS threshold")
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Similarity threshold")
    
    # Project settings
    project_root: Optional[Path] = Field(None, description="Project root directory")
    sut_package: Optional[str] = Field(None, description="System under test package")
    test_patterns: List[str] = Field(
        default_factory=lambda: ["test_*.py", "*_test.py"], 
        description="Test file patterns"
    )
    ignore_patterns: List[str] = Field(
        default_factory=list, 
        description="Files/patterns to ignore"
    )
    
    # Per-file ignores
    per_file_ignores: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Rule ignores per file pattern"
    )
    
    # Advanced file controls
    include_patterns: List[str] = Field(
        default_factory=list,
        description="Additional include patterns for file discovery"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="Additional exclude patterns for file discovery"
    )
    per_file_severity_overrides: Dict[str, SeverityLevel] = Field(
        default_factory=dict,
        description="Severity overrides per file pattern"
    )
    per_file_rule_overrides: Dict[str, Dict[str, RuleConfig]] = Field(
        default_factory=dict,
        description="Rule configuration overrides per file pattern"
    )
    
    @field_validator("rules")
    @classmethod
    def validate_rule_codes(cls, v: Dict[str, RuleConfig]) -> Dict[str, RuleConfig]:
        """Validate that rule keys are valid rule codes."""
        from pytest_drill_sergeant.core.rulespec import RuleRegistry
        
        for rule_code in v.keys():
            if not RuleRegistry.is_valid_rule(rule_code):
                suggestions = _suggest_rule_codes(rule_code)
                if suggestions:
                    raise ValueError(
                        f"Invalid rule code '{rule_code}'. "
                        f"Did you mean: {', '.join(suggestions)}?"
                    )
                else:
                    raise ValueError(f"Invalid rule code '{rule_code}'. Use 'DS###' format.")
        return v
    
    @field_validator("per_file_ignores")
    @classmethod
    def validate_per_file_ignores(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate per-file ignore patterns."""
        from pytest_drill_sergeant.core.rulespec import RuleRegistry
        
        for pattern, rule_codes in v.items():
            if not pattern.strip():
                raise ValueError("File patterns cannot be empty")
            
            for rule_code in rule_codes:
                if not RuleRegistry.is_valid_rule(rule_code):
                    suggestions = _suggest_rule_codes(rule_code)
                    if suggestions:
                        raise ValueError(
                            f"Invalid rule code '{rule_code}' in per_file_ignores. "
                            f"Did you mean: {', '.join(suggestions)}?"
                        )
                    else:
                        raise ValueError(f"Invalid rule code '{rule_code}'. Use 'DS###' format.")
        return v
    
    @field_validator("test_patterns", "ignore_patterns", "include_patterns", "exclude_patterns")
    @classmethod
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """Validate file patterns."""
        for pattern in v:
            if not pattern.strip():
                raise ValueError("File patterns cannot be empty")
        return v
    
    @field_validator("per_file_severity_overrides")
    @classmethod
    def validate_per_file_severity_overrides(cls, v: Dict[str, SeverityLevel]) -> Dict[str, SeverityLevel]:
        """Validate per-file severity overrides."""
        for pattern in v.keys():
            if not pattern.strip():
                raise ValueError("File patterns cannot be empty")
        return v
    
    @field_validator("per_file_rule_overrides")
    @classmethod
    def validate_per_file_rule_overrides(cls, v: Dict[str, Dict[str, RuleConfig]]) -> Dict[str, Dict[str, RuleConfig]]:
        """Validate per-file rule overrides."""
        from pytest_drill_sergeant.core.rulespec import RuleRegistry
        
        for pattern, rule_configs in v.items():
            if not pattern.strip():
                raise ValueError("File patterns cannot be empty")
            
            for rule_code, rule_config in rule_configs.items():
                if not RuleRegistry.is_valid_rule(rule_code):
                    suggestions = _suggest_rule_codes(rule_code)
                    if suggestions:
                        raise ValueError(
                            f"Invalid rule code '{rule_code}' in per_file_rule_overrides. "
                            f"Did you mean: {', '.join(suggestions)}?"
                        )
                    else:
                        raise ValueError(f"Invalid rule code '{rule_code}'. Use 'DS###' format.")
        return v
    
    @model_validator(mode="after")
    def validate_profile_exists(self) -> "DSConfig":
        """Validate that the active profile exists."""
        if self.profile.value not in self.profiles:
            available_profiles = list(self.profiles.keys()) + ["standard", "strict", "relaxed"]
            raise ValueError(
                f"Profile '{self.profile.value}' not found in profiles. "
                f"Available profiles: {', '.join(available_profiles)}"
            )
        return self
    
    @model_validator(mode="after")
    def validate_output_paths(self) -> "DSConfig":
        """Validate output file paths."""
        if self.output.format == OutputFormat.JSON and not self.output.json_path:
            raise ValueError("json_path is required when format is 'json'")
        
        if self.output.format == OutputFormat.SARIF and not self.output.sarif_path:
            raise ValueError("sarif_path is required when format is 'sarif'")
        
        return self


def _suggest_rule_codes(invalid_code: str) -> List[str]:
    """Suggest similar rule codes for invalid input."""
    from pytest_drill_sergeant.core.rulespec import RuleRegistry
    
    suggestions = []
    all_rules = RuleRegistry.get_all_rules()
    
    # Exact name match
    for rule in all_rules:
        if rule.name == invalid_code:
            suggestions.append(rule.code)
    
    # Partial code match
    if invalid_code.startswith("DS"):
        for rule in all_rules:
            if rule.code.startswith(invalid_code):
                suggestions.append(rule.code)
    
    # Partial name match
    for rule in all_rules:
        if invalid_code.lower() in rule.name.lower():
            suggestions.append(rule.code)
    
    # Fuzzy matching for common typos
    common_typos = {
        "private": "DS301",
        "duplicate": "DS201", 
        "fixture": "DS202",
        "mock": "DS204",
        "aaa": "DS302",
        "clone": "DS303",
    }
    
    for typo, code in common_typos.items():
        if typo in invalid_code.lower():
            suggestions.append(code)
    
    return list(set(suggestions))[:3]  # Return up to 3 suggestions


def validate_config(config_data: Dict[str, Any]) -> DSConfig:
    """Validate configuration data with helpful error messages.
    
    Args:
        config_data: Raw configuration data
        
    Returns:
        Validated DSConfig instance
        
    Raises:
        ValidationError: If configuration is invalid
    """
    return DSConfig.model_validate(config_data)


def _suggest_field_name(invalid_field: str) -> List[str]:
    """Suggest similar field names for invalid input."""
    valid_fields = [
        "schema_version", "profile", "profiles", "analysis", "output", "rules",
        "bis_threshold", "brs_threshold", "similarity_threshold", "project_root",
        "sut_package", "test_patterns", "ignore_patterns", "per_file_ignores"
    ]
    
    suggestions = []
    
    # Exact match (case insensitive)
    for field in valid_fields:
        if field.lower() == invalid_field.lower():
            suggestions.append(field)
    
    # Partial match
    for field in valid_fields:
        if invalid_field.lower() in field.lower():
            suggestions.append(field)
    
    # Common typos
    common_typos = {
        "threshold": ["bis_threshold", "brs_threshold", "similarity_threshold"],
        "pattern": ["test_patterns", "ignore_patterns"],
        "ignore": ["ignore_patterns", "per_file_ignores"],
        "rule": ["rules"],
        "profile": ["profile", "profiles"],
    }
    
    for typo, fields in common_typos.items():
        if typo in invalid_field.lower():
            suggestions.extend(fields)
    
    return list(set(suggestions))[:3]


def create_default_config() -> DSConfig:
    """Create a default configuration with standard profile."""
    from pytest_drill_sergeant.core.rulespec import RuleRegistry
    
    # Create default rule configurations
    default_rules = {}
    for rule in RuleRegistry.get_all_rules():
        default_rules[rule.code] = RuleConfig(
            enabled=True,
            severity=rule.default_level,
            threshold=None,
            tags=rule.tags.copy(),
            metadata={}
        )
    
    # Create standard profile
    standard_profile = ProfileConfig(
        name="standard",
        description="Standard configuration with balanced rules",
        rules=default_rules.copy(),
        thresholds={
            "bis_threshold": 70.0,
            "brs_threshold": 60.0,
            "similarity_threshold": 0.8,
        },
        settings={
            "strict_mode": False,
            "auto_fix": False,
        }
    )
    
    # Create strict profile
    strict_rules = default_rules.copy()
    for rule_code, rule_config in strict_rules.items():
        rule_config.severity = SeverityLevel.ERROR if rule_config.severity == SeverityLevel.WARNING else rule_config.severity
    
    strict_profile = ProfileConfig(
        name="strict",
        description="Strict configuration with higher standards",
        rules=strict_rules,
        thresholds={
            "bis_threshold": 85.0,
            "brs_threshold": 75.0,
            "similarity_threshold": 0.9,
        },
        settings={
            "strict_mode": True,
            "auto_fix": True,
        }
    )
    
    # Create relaxed profile
    relaxed_rules = default_rules.copy()
    for rule_code, rule_config in relaxed_rules.items():
        if rule_config.severity == SeverityLevel.ERROR:
            rule_config.severity = SeverityLevel.WARNING
        elif rule_config.severity == SeverityLevel.WARNING:
            rule_config.severity = SeverityLevel.INFO
    
    relaxed_profile = ProfileConfig(
        name="relaxed",
        description="Relaxed configuration with lower standards",
        rules=relaxed_rules,
        thresholds={
            "bis_threshold": 50.0,
            "brs_threshold": 40.0,
            "similarity_threshold": 0.7,
        },
        settings={
            "strict_mode": False,
            "auto_fix": False,
        }
    )
    
    return DSConfig(
        schema_version=SchemaVersion.V1_0,
        profile=Profile.STANDARD,
        profiles={
            "standard": standard_profile,
            "strict": strict_profile,
            "relaxed": relaxed_profile,
        },
        analysis=AnalysisConfig(),
        output=OutputConfig(),
        rules=default_rules,
        bis_threshold=70.0,
        brs_threshold=60.0,
        similarity_threshold=0.8,
        test_patterns=["test_*.py", "*_test.py"],
        ignore_patterns=[],
        per_file_ignores={},
        include_patterns=[],
        exclude_patterns=[],
        per_file_severity_overrides={},
        per_file_rule_overrides={},
    )
