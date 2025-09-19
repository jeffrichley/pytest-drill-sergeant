"""Tests for the strict configuration schema."""

import pytest
from pydantic import ValidationError

from pytest_drill_sergeant.core.config_schema import (
    AnalysisConfig,
    DSConfig,
    OutputConfig,
    OutputFormat,
    Profile,
    ProfileConfig,
    RuleConfig,
    SchemaVersion,
    SeverityLevel,
    create_default_config,
    validate_config,
)


class TestRuleConfig:
    """Test RuleConfig validation."""

    def test_valid_rule_config(self):
        """Test creating a valid rule configuration."""
        config = RuleConfig(
            enabled=True,
            severity=SeverityLevel.WARNING,
            threshold=0.8,
            tags=["quality", "test"],
            metadata={"custom": "value"},
        )

        assert config.enabled is True
        assert config.severity == SeverityLevel.WARNING
        assert config.threshold == 0.8
        assert config.tags == ["quality", "test"]
        assert config.metadata == {"custom": "value"}

    def test_rule_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in RuleConfig."""
        with pytest.raises(ValidationError) as exc_info:
            RuleConfig(enabled=True, invalid_field="should_fail")

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)

    def test_rule_config_invalid_threshold(self):
        """Test validation of threshold values."""
        with pytest.raises(ValidationError) as exc_info:
            RuleConfig(
                enabled=True,
                threshold=1.5,  # Invalid: > 1.0
            )

        error = exc_info.value
        assert "less than or equal to 1" in str(error)

    def test_rule_config_invalid_tags(self):
        """Test validation of tags."""
        with pytest.raises(ValidationError) as exc_info:
            RuleConfig(
                enabled=True,
                tags=["valid", "", "invalid"],  # Empty string should fail
            )

        error = exc_info.value
        assert "Tags must be non-empty strings" in str(error)


class TestProfileConfig:
    """Test ProfileConfig validation."""

    def test_valid_profile_config(self):
        """Test creating a valid profile configuration."""
        config = ProfileConfig(
            name="test_profile",
            description="Test profile for testing",
            rules={
                "DS201": RuleConfig(enabled=True, severity=SeverityLevel.WARNING),
                "DS301": RuleConfig(enabled=False),
            },
            thresholds={"bis_threshold": 80.0},
            settings={"strict_mode": True},
        )

        assert config.name == "test_profile"
        assert len(config.rules) == 2
        assert "DS201" in config.rules
        assert "DS301" in config.rules

    def test_profile_config_invalid_rule_code(self):
        """Test validation of invalid rule codes in profile."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileConfig(
                name="test_profile",
                description="Test profile",
                rules={"INVALID": RuleConfig(enabled=True)},  # Invalid rule code
            )

        error = exc_info.value
        assert "Invalid rule code 'INVALID'" in str(error)

    def test_profile_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in ProfileConfig."""
        with pytest.raises(ValidationError) as exc_info:
            ProfileConfig(
                name="test_profile",
                description="Test profile",
                invalid_field="should_fail",
            )

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)


class TestOutputConfig:
    """Test OutputConfig validation."""

    def test_valid_output_config(self):
        """Test creating a valid output configuration."""
        config = OutputConfig(
            format=OutputFormat.JSON, json_path="output.json", verbose=True, color=False
        )

        assert config.format == OutputFormat.JSON
        assert str(config.json_path) == "output.json"
        assert config.verbose is True
        assert config.color is False

    def test_output_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in OutputConfig."""
        with pytest.raises(ValidationError) as exc_info:
            OutputConfig(format=OutputFormat.TERMINAL, invalid_field="should_fail")

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)


class TestAnalysisConfig:
    """Test AnalysisConfig validation."""

    def test_valid_analysis_config(self):
        """Test creating a valid analysis configuration."""
        config = AnalysisConfig(
            parallel=True,
            max_workers=8,
            cache_ast=False,
            timeout=30.0,
            memory_limit=512,
        )

        assert config.parallel is True
        assert config.max_workers == 8
        assert config.cache_ast is False
        assert config.timeout == 30.0
        assert config.memory_limit == 512

    def test_analysis_config_invalid_workers(self):
        """Test validation of max_workers."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisConfig(max_workers=0)  # Invalid: < 1

        error = exc_info.value
        assert "greater than or equal to 1" in str(error)

    def test_analysis_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in AnalysisConfig."""
        with pytest.raises(ValidationError) as exc_info:
            AnalysisConfig(parallel=True, invalid_field="should_fail")

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)


class TestDSConfig:
    """Test main DSConfig validation."""

    def test_valid_ds_config(self):
        """Test creating a valid DSConfig."""
        config = DSConfig(
            schema_version=SchemaVersion.V1_0,
            profile=Profile.STANDARD,
            profiles={
                "standard": ProfileConfig(
                    name="standard", description="Standard profile"
                )
            },
            bis_threshold=75.0,
            brs_threshold=65.0,
            similarity_threshold=0.85,
        )

        assert config.schema_version == SchemaVersion.V1_0
        assert config.profile == Profile.STANDARD
        assert config.bis_threshold == 75.0

    def test_ds_config_extra_fields_forbidden(self):
        """Test that extra fields are forbidden in DSConfig."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={},
                invalid_field="should_fail",
            )

        error = exc_info.value
        assert "Extra inputs are not permitted" in str(error)

    def test_ds_config_invalid_rule_codes(self):
        """Test validation of invalid rule codes."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={},
                rules={"INVALID": RuleConfig(enabled=True)},
            )

        error = exc_info.value
        assert "Invalid rule code 'INVALID'" in str(error)

    def test_ds_config_invalid_per_file_ignores(self):
        """Test validation of per_file_ignores."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={},
                per_file_ignores={"tests/**": ["INVALID"]},  # Invalid rule code
            )

        error = exc_info.value
        assert "Invalid rule code 'INVALID'" in str(error)

    def test_ds_config_empty_patterns(self):
        """Test validation of empty file patterns."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={},
                test_patterns=[""],  # Empty pattern
            )

        error = exc_info.value
        assert "File patterns cannot be empty" in str(error)

    def test_ds_config_profile_not_found(self):
        """Test validation when active profile doesn't exist."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STRICT,
                profiles={
                    "standard": ProfileConfig(
                        name="standard", description="Standard profile"
                    )
                },
            )

        error = exc_info.value
        assert "Profile 'strict' not found" in str(error)

    def test_ds_config_output_path_validation(self):
        """Test validation of output paths."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={
                    "standard": ProfileConfig(
                        name="standard", description="Standard profile"
                    )
                },
                output=OutputConfig(
                    format=OutputFormat.JSON,
                    # Missing json_path
                ),
            )

        error = exc_info.value
        assert "json_path is required when format is 'json'" in str(error)


class TestValidateConfig:
    """Test the validate_config function."""

    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        config_data = {
            "schema_version": "1.0",
            "profile": "standard",
            "profiles": {
                "standard": {"name": "standard", "description": "Standard profile"}
            },
            "bis_threshold": 70.0,
            "brs_threshold": 60.0,
            "similarity_threshold": 0.8,
        }

        config = validate_config(config_data)
        assert isinstance(config, DSConfig)
        assert config.profile == Profile.STANDARD

    def test_validate_invalid_config_with_suggestions(self):
        """Test validation with helpful error suggestions."""
        config_data = {
            "schema_version": "1.0",
            "profile": "standard",
            "profiles": {
                "standard": {"name": "standard", "description": "Standard profile"}
            },
            "invalid_field": "should_fail",  # Extra field
            "rules": {"INVALID": {"enabled": True}},  # Invalid rule code
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config_data)

        error = exc_info.value
        error_str = str(error)

        # Should have error for invalid field
        assert "invalid_field" in error_str
        assert "Extra inputs are not permitted" in error_str

        # Should have error for invalid rule code
        assert "Invalid rule code 'INVALID'" in error_str


class TestCreateDefaultConfig:
    """Test the create_default_config function."""

    def test_create_default_config(self):
        """Test creating a default configuration."""
        config = create_default_config()

        assert isinstance(config, DSConfig)
        assert config.schema_version == SchemaVersion.V1_0
        assert config.profile == Profile.STANDARD
        assert len(config.profiles) == 3  # standard, strict, relaxed
        assert "standard" in config.profiles
        assert "strict" in config.profiles
        assert "relaxed" in config.profiles

        # Check that rules are properly configured
        assert len(config.rules) > 0
        for rule_code, rule_config in config.rules.items():
            assert rule_code.startswith("DS")
            assert isinstance(rule_config, RuleConfig)

    def test_default_profiles_differ(self):
        """Test that default profiles have different configurations."""
        config = create_default_config()

        standard = config.profiles["standard"]
        strict = config.profiles["strict"]
        relaxed = config.profiles["relaxed"]

        # Strict should have higher thresholds
        assert strict.thresholds["bis_threshold"] > standard.thresholds["bis_threshold"]
        assert strict.thresholds["brs_threshold"] > standard.thresholds["brs_threshold"]

        # Relaxed should have lower thresholds
        assert (
            relaxed.thresholds["bis_threshold"] < standard.thresholds["bis_threshold"]
        )
        assert (
            relaxed.thresholds["brs_threshold"] < standard.thresholds["brs_threshold"]
        )


class TestSchemaVersioning:
    """Test schema versioning functionality."""

    def test_schema_version_required(self):
        """Test that schema version has a default value."""
        # Schema version should have a default value, so this should work
        config = DSConfig(
            profile=Profile.STANDARD,
            profiles={
                "standard": ProfileConfig(
                    name="standard", description="Standard profile"
                )
            },
        )

        # Should have default schema version
        assert config.schema_version == SchemaVersion.V1_0

    def test_schema_version_validation(self):
        """Test that only valid schema versions are accepted."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version="2.0",  # Invalid version
                profile=Profile.STANDARD,
                profiles={},
            )

        error = exc_info.value
        assert "Input should be '1.0'" in str(error)


class TestErrorMessages:
    """Test quality of error messages."""

    def test_helpful_rule_code_suggestions(self):
        """Test that rule code errors provide helpful suggestions."""
        with pytest.raises(ValidationError) as exc_info:
            DSConfig(
                schema_version=SchemaVersion.V1_0,
                profile=Profile.STANDARD,
                profiles={},
                rules={"private": RuleConfig(enabled=True)},  # Should suggest DS301
            )

        error = exc_info.value
        error_str = str(error)
        assert "private" in error_str
        assert "DS301" in error_str  # Should suggest the correct code

    def test_helpful_field_suggestions(self):
        """Test that field errors provide helpful suggestions."""
        config_data = {
            "schema_version": "1.0",
            "profile": "standard",
            "profiles": {
                "standard": {"name": "standard", "description": "Standard profile"}
            },
            "threshhold": 70.0,  # Typo: should be "threshold"
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_config(config_data)

        error = exc_info.value
        error_str = str(error)
        assert "threshhold" in error_str
        assert "Extra inputs are not permitted" in error_str
