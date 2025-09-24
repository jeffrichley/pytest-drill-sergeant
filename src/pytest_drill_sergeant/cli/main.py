"""CLI entry point for pytest-drill-sergeant."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

from pytest_drill_sergeant.core.logging_utils import get_logger, setup_logging

app = typer.Typer(help="pytest-drill-sergeant: AI test quality enforcement")


@dataclass
class LintConfig:
    """Configuration for lint command."""

    paths: list[str]
    profile: str = "standard"
    enable: str | None = None
    disable: str | None = None
    only: str | None = None
    fail_on: str = "error"
    treat: str | None = None
    output_format: str = "terminal"
    output: str | None = None
    config: str | None = None
    persona: str = "drill_sergeant"
    sut_filter: str | None = None
    rich_output: bool = True


class AnalysisContext:
    """Context manager for analysis operations, replacing global state."""

    def __init__(self):
        from pytest_drill_sergeant.plugin.analysis_storage import AnalysisStorage
        from pytest_drill_sergeant.plugin.personas.manager import get_persona_manager

        self.storage = AnalysisStorage()
        self.persona_manager = get_persona_manager()
        self.analyzers = []
        self.sut_filter = None

    def add_analyzer(self, analyzer):
        """Add an analyzer to the context."""
        self.storage.add_analyzer(analyzer)
        self.analyzers.append(analyzer)

    def set_sut_filter(self, sut_pattern: str | None):
        """Set the SUT filter pattern."""
        self.sut_filter = SUTFilter(sut_pattern)

    def analyze_file(self, path: Path) -> list:
        """Analyze a single file using the analysis pipeline."""
        # Use the analysis pipeline directly instead of storage
        findings = []
        for analyzer in self.analyzers:
            try:
                analyzer_findings = analyzer.analyze_file(path)
                findings.extend(analyzer_findings)
            except Exception as e:
                # Log error but continue with other analyzers
                print(f"Error in {type(analyzer).__name__}: {e}")
        return findings

    def filter_findings_by_severity(self, findings: list, profile_config=None) -> list:
        """Filter findings based on profile fail-on setting."""
        # Use centralized config context
        try:
            from pytest_drill_sergeant.core.config_context import (
                should_fail_on_severity,
            )

            should_fail_func = should_fail_on_severity
        except ImportError:
            # Fallback to passed-in config
            if not profile_config:
                return findings
            should_fail_func = profile_config.should_fail_on_severity

        filtered_findings = []
        for finding in findings:
            # Check if this severity should be included based on fail-on setting
            should_include = should_fail_func(finding.severity)
            if should_include:
                filtered_findings.append(finding)

        # Debug logging
        if findings and len(filtered_findings) != len(findings):
            logger = logging.getLogger(__name__)
            try:
                from pytest_drill_sergeant.core.config_context import get_fail_on_level

                fail_on = get_fail_on_level().value
            except ImportError:
                fail_on = profile_config.fail_on.value if profile_config else "unknown"
            logger.debug(
                "Filtered %d findings to %d based on fail-on=%s",
                len(findings),
                len(filtered_findings),
                fail_on,
            )

        return filtered_findings

    def get_files_to_analyze(self, base_path: Path) -> list[Path]:
        """Get list of files to analyze based on SUT filter."""
        if self.sut_filter:
            return self.sut_filter.get_analysis_scope(base_path)
        # Default: analyze all Python files
        all_files = list(base_path.rglob("*.py"))
        return [
            f
            for f in all_files
            if not any(
                part.startswith(".") or part == "__pycache__" for part in f.parts
            )
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


class SUTFilter:
    """Filters test files based on SUT (System Under Test) path patterns."""

    def __init__(self, sut_pattern: str | None = None):
        """Initialize the SUT filter.

        Args:
            sut_pattern: Path pattern to filter by (e.g., 'unit', 'unit/utils', 'e2e')
        """
        self.sut_pattern = sut_pattern

    def should_analyze(self, file_path: Path, base_path: Path) -> bool:
        """Check if a file should be analyzed based on SUT filter.

        Args:
            file_path: Path to the file to check
            base_path: Base path for relative comparisons

        Returns:
            True if file should be analyzed, False otherwise
        """
        if not self.sut_pattern:
            return True  # Analyze everything by default

        try:
            # Get relative path from base
            rel_path = file_path.relative_to(base_path)

            # Check if file is under the SUT pattern
            if str(rel_path).startswith(self.sut_pattern):
                return True

            # Also check if any parent directory matches
            for parent in rel_path.parents:
                if str(parent) == self.sut_pattern:
                    return True

            return False

        except ValueError:
            # File is not under base_path
            return False

    def get_analysis_scope(self, base_path: Path) -> list[Path]:
        """Get list of files to analyze based on SUT filter.

        Args:
            base_path: Base directory to search from

        Returns:
            List of Python files to analyze
        """
        if not self.sut_pattern:
            # No SUT filter specified - analyze everything in the paths
            all_files = list(base_path.rglob("*.py"))
            return [
                f
                for f in all_files
                if not any(
                    part.startswith(".") or part == "__pycache__" for part in f.parts
                )
            ]

        # SUT filter specified - only analyze files under the SUT pattern
        sut_path = base_path / self.sut_pattern

        if sut_path.exists():
            # SUT path exists, analyze files under it
            return list(sut_path.rglob("*.py"))
        # SUT path doesn't exist, return empty list
        return []


def _run_lint_with_options(opts: LintConfig) -> int:
    """Execute the lint analysis with the given configuration."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=opts.rich_output)
    logger = get_logger(__name__)

    # Initialize error handling
    from pytest_drill_sergeant.core.error_handler import get_error_handler
    error_handler = get_error_handler()

    # Initialize centralized configuration
    from pytest_drill_sergeant.core.config_context import get_config, initialize_config
    from pytest_drill_sergeant.core.config_validator_enhanced import (
        EnhancedConfigValidator,
    )

    # Convert CLI options to config dict
    cli_config = {
        "version": "1.0",  # Required field for validation
        "profile": opts.profile,
        "fail_on": opts.fail_on,
        "output_formats": [opts.output_format],
        "verbose": not opts.rich_output,  # Plain output = verbose
        "quiet": False,
    }

    if opts.output:
        cli_config["json_report_path"] = opts.output

    # Handle rule overrides from --treat option
    if opts.treat:
        treat_overrides = {}
        for rule_override in opts.treat.split(","):
            if ":" in rule_override:
                rule_name, severity = rule_override.split(":", 1)
                treat_overrides[rule_name.strip()] = {"level": severity.strip()}
        if treat_overrides:
            cli_config["rules"] = treat_overrides

    # Validate configuration
    config_validator = EnhancedConfigValidator()
    validation_errors = config_validator.validate_config(cli_config)
    
    if validation_errors:
        typer.echo("❌ Configuration validation errors:")
        for error in validation_errors:
            typer.echo(f"  • {error.message}")
            if error.suggestion:
                typer.echo(f"    💡 Suggestion: {error.suggestion}")
        return 1

    # Initialize configuration
    try:
        initialize_config(cli_args=cli_config)
        profile_config = get_config()
    except Exception as e:
        logger.error("Failed to load configuration: %s", e)
        typer.echo(f"❌ Configuration error: {e}")
        return 1

    logger.info("Starting analysis...")
    logger.info(
        "Analyzing %d paths with %s profile",
        len(opts.paths),
        profile_config.profile.value,
    )
    logger.info("Active profile: %s", profile_config.profile.value)
    logger.info("Fail on: %s", "error")  # DSConfig always fails on error

    # Debug: Show private_access rule configuration
    private_access_rule = profile_config.rules.get("private_access")
    if private_access_rule:
        logger.info(
            "Private access rule severity: %s",
            (
                private_access_rule.severity.value
                if private_access_rule.severity
                else "default"
            ),
        )
        logger.info("Private access rule enabled: %s", private_access_rule.enabled)
    else:
        logger.info("Private access rule: not configured")

    # Debug: Show profile configuration details
    logger.info("Available profiles: %s", list(profile_config.profiles.keys()))
    if "strict" in profile_config.profiles:
        strict_rules = profile_config.profiles["strict"].rules
        logger.info("Strict profile rules: %s", list(strict_rules.keys()))
        if "private_access" in strict_rules:
            logger.info(
                "Strict private_access level: %s",
                (
                    strict_rules["private_access"].severity.value
                    if strict_rules["private_access"].severity
                    else "default"
                ),
            )

    try:
        # Import our analysis components
        from pathlib import Path

        from pytest_drill_sergeant.core.analysis_pipeline import (
            create_analysis_pipeline,
        )

        # Use context manager instead of globals
        with AnalysisContext() as ctx:
            # Set up SUT filter
            ctx.set_sut_filter(opts.sut_filter)

            # Create centralized analysis pipeline with error handling
            pipeline = create_analysis_pipeline()
            
            # Add the pipeline to context (context will handle individual analyzers)
            for analyzer in pipeline.analyzers:
                ctx.add_analyzer(analyzer)

            # Analyze each path
            total_violations = 0
            total_files = 0
            all_findings = []
            all_bis_scores = []
            files_analyzed = []

            for path_str in opts.paths:
                path = Path(path_str)

                if path.is_file():
                    # Analyze single file with error handling
                    findings, file_errors = pipeline.analyze_file(path)
                    
                    # Report any analysis errors
                    if file_errors:
                        typer.echo(f"\n⚠️  Analysis errors in {path}:")
                        for error in file_errors:
                            typer.echo(f"  • {error.message}")
                            if error.suggestion:
                                typer.echo(f"    💡 Suggestion: {error.suggestion}")
                    
                    # In advisory mode, show all findings; in strict mode, filter by severity
                    if opts.fail_on == "error":
                        # Advisory mode - show all findings but don't fail on warnings
                        display_findings = findings
                        filtered_findings = ctx.filter_findings_by_severity(findings)
                        total_violations += len(filtered_findings)  # Only count failures for exit code
                    else:
                        # Strict mode - filter and count all
                        display_findings = ctx.filter_findings_by_severity(findings)
                        filtered_findings = display_findings
                        total_violations += len(filtered_findings)
                    
                    total_files += 1

                    # Calculate BIS score for this file
                    from pytest_drill_sergeant.core.scoring import DynamicBISCalculator
                    bis_calculator = DynamicBISCalculator()
                    metrics = bis_calculator.extract_metrics_from_findings(findings)
                    bis_score = bis_calculator.calculate_bis(metrics)
                    bis_grade = bis_calculator.get_grade(bis_score)
                    
                    # Collect data for BRS calculation
                    all_findings.extend(findings)
                    all_bis_scores.append(bis_score)
                    files_analyzed.append(path)
                    
                    # Display results for this file
                    if display_findings:
                        typer.echo(f"\n🔍 Analyzing: {path}")
                        for i, finding in enumerate(display_findings, 1):
                            # Use appropriate message based on severity
                            severity_str = finding.severity if isinstance(finding.severity, str) else finding.severity.value
                            if severity_str in ["error"]:
                                message = ctx.persona_manager.on_test_fail(
                                    f"{path.name}:{finding.line_number}", finding
                                )
                                typer.echo(f"  ❌ {i}. {message}")
                            else:
                                # For warnings/info, show advisory message with IDE-clickable format
                                typer.echo(f"  ⚠️  {i}. {path}:{finding.line_number}: {finding.message}")
                        
                        # Show BIS score
                        typer.echo(f"  📊 BIS Score: {bis_score:.1f} ({bis_grade}) - {bis_calculator.get_score_interpretation(bis_score)}")
                    else:
                        success_msg = ctx.persona_manager.on_test_pass(str(path))
                        typer.echo(f"\n✅ {success_msg}")
                        typer.echo(f"  📊 BIS Score: {bis_score:.1f} ({bis_grade}) - {bis_calculator.get_score_interpretation(bis_score)}")

                elif path.is_dir():
                    # Use SUT filter to get files to analyze
                    files_to_analyze = ctx.get_files_to_analyze(path)

                    if not files_to_analyze:
                        typer.echo(f"⚠️  No Python files found in {path}")
                        continue

                    # Show filter info if SUT filter is active
                    if opts.sut_filter:
                        typer.echo(
                            f"\n📁 Analyzing directory: {path} (SUT filter: {opts.sut_filter})"
                        )
                        typer.echo(
                            f"   Found {len(files_to_analyze)} files matching filter"
                        )
                    else:
                        typer.echo(
                            f"\n📁 Analyzing directory: {path} ({len(files_to_analyze)} Python files)"
                        )

                    for py_file in files_to_analyze:
                        findings, file_errors = pipeline.analyze_file(py_file)
                        
                        # Report any analysis errors
                        if file_errors:
                            typer.echo(f"\n  ⚠️  Analysis errors in {py_file.relative_to(path)}:")
                            for error in file_errors:
                                typer.echo(f"    • {error.message}")
                                if error.suggestion:
                                    typer.echo(f"      💡 Suggestion: {error.suggestion}")
                        
                        # In advisory mode, show all findings; in strict mode, filter by severity
                        if opts.fail_on == "error":
                            # Advisory mode - show all findings but don't fail on warnings
                            display_findings = findings
                            filtered_findings = ctx.filter_findings_by_severity(findings)
                            total_violations += len(filtered_findings)  # Only count failures for exit code
                        else:
                            # Strict mode - filter and count all
                            display_findings = ctx.filter_findings_by_severity(findings)
                            filtered_findings = display_findings
                            total_violations += len(filtered_findings)
                        
                        total_files += 1

                        # Calculate BIS score for this file
                        from pytest_drill_sergeant.core.scoring import (
                            DynamicBISCalculator,
                        )
                        bis_calculator = DynamicBISCalculator()
                        metrics = bis_calculator.extract_metrics_from_findings(findings)
                        bis_score = bis_calculator.calculate_bis(metrics)
                        bis_grade = bis_calculator.get_grade(bis_score)
                        
                        # Collect data for BRS calculation
                        all_findings.extend(findings)
                        all_bis_scores.append(bis_score)
                        files_analyzed.append(py_file)
                        
                        if display_findings:
                            typer.echo(f"\n  🔍 {py_file.relative_to(path)}")
                            for i, finding in enumerate(display_findings, 1):
                                # Use appropriate message based on severity
                                severity_str = finding.severity if isinstance(finding.severity, str) else finding.severity.value
                                if severity_str in ["error"]:
                                    message = ctx.persona_manager.on_test_fail(
                                        f"{py_file.name}:{finding.line_number}", finding
                                    )
                                    typer.echo(f"    ❌ {i}. {message}")
                                else:
                                    # For warnings/info, show advisory message with IDE-clickable format
                                    typer.echo(f"    ⚠️  {i}. {py_file}:{finding.line_number}: {finding.message}")
                            
                            # Show BIS score
                            typer.echo(f"    📊 BIS Score: {bis_score:.1f} ({bis_grade}) - {bis_calculator.get_score_interpretation(bis_score)}")
                        else:
                            # Show BIS score for clean files too
                            typer.echo(f"  ✅ {py_file.relative_to(path)} - BIS Score: {bis_score:.1f} ({bis_grade})")
                else:
                    typer.echo(f"⚠️  Path not found: {path}")
                    continue

            # Calculate BRS score
            from pytest_drill_sergeant.core.scoring import BRSCalculator
            brs_calculator = BRSCalculator()
            metrics = brs_calculator.extract_metrics_from_analysis(files_analyzed, all_findings, all_bis_scores)
            brs_score = brs_calculator.calculate_brs(metrics)
            brs_grade = brs_calculator.get_brs_grade(brs_score)
            brs_interpretation = brs_calculator.get_brs_interpretation(brs_score)
            
            # Display summary
            typer.echo(f"\n{'='*60}")
            summary_msg = ctx.persona_manager.on_summary(
                type(
                    "MockMetrics",
                    (),
                    {
                        "total_tests": total_files,
                        "total_violations": total_violations,
                        "brs_score": brs_score,
                    },
                )()
            )
            typer.echo(f"🎖️  {summary_msg}")
            typer.echo(f"📊 BRS Score: {brs_score:.1f} ({brs_grade}) - {brs_interpretation}")

            typer.echo(f"📊 Total violations found: {total_violations}")
            typer.echo(f"📁 Files analyzed: {total_files}")

            # Display error summary if there were any analysis errors
            analysis_errors = pipeline.get_analysis_errors()
            if analysis_errors:
                typer.echo(f"\n⚠️  Analysis errors encountered: {len(analysis_errors)}")
                error_summary = pipeline.get_error_summary()
                typer.echo(f"   • Critical errors: {error_summary.get('critical_errors', 0)}")
                typer.echo(f"   • Recoverable errors: {error_summary.get('recoverable_errors', 0)}")
                
                # Show error breakdown by category
                by_category = error_summary.get("by_category", {})
                if by_category:
                    typer.echo("   • Errors by category:")
                    for category, count in by_category.items():
                        typer.echo(f"     - {category}: {count}")

            return 0 if total_violations == 0 else 1

    except Exception as e:
        logger.error("Analysis failed: %s", e)
        typer.echo(f"❌ Analysis failed: {e}")
        return 1


@app.command()
def lint(  # noqa: PLR0913
    paths: Annotated[
        list[str], typer.Argument(..., help="Test files or directories to analyze")
    ],
    profile: Annotated[
        str, typer.Option("--profile", help="Profile to use: chill, standard, strict")
    ] = "standard",
    enable: Annotated[
        str | None,
        typer.Option("--enable", help="Comma-separated list of rules to enable"),
    ] = None,
    disable: Annotated[
        str | None,
        typer.Option("--disable", help="Comma-separated list of rules to disable"),
    ] = None,
    only: Annotated[
        str | None,
        typer.Option(
            "--only", help="Comma-separated list of rules to run (disables all others)"
        ),
    ] = None,
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on", help="Severity level to fail on: error, warning, info"
        ),
    ] = "error",
    treat: Annotated[
        str | None,
        typer.Option(
            "--treat",
            help="Override rule severities (e.g., 'duplicate_tests:error,overmocking:info')",
        ),
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format")
    ] = "terminal",
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Output file path")
    ] = None,
    config: Annotated[
        str | None, typer.Option("--config", "-c", help="Configuration file")
    ] = None,
    persona: Annotated[
        str, typer.Option("--persona", help="Persona to use")
    ] = "drill_sergeant",
    sut_filter: Annotated[
        str | None,
        typer.Option(
            "--sut-filter", help="SUT path filter (e.g., 'unit', 'unit/utils', 'e2e')"
        ),
    ] = None,
    rich_output: Annotated[
        bool, typer.Option("--rich/--plain", help="Use rich output formatting")
    ] = True,
) -> None:
    """Analyze test files for quality issues."""
    # Create configuration and execute
    opts = LintConfig(
        paths=paths,
        profile=profile,
        enable=enable,
        disable=disable,
        only=only,
        fail_on=fail_on,
        treat=treat,
        output_format=output_format,
        output=output,
        config=config,
        persona=persona,
        sut_filter=sut_filter,
        rich_output=rich_output,
    )
    raise typer.Exit(code=_run_lint_with_options(opts))


@app.command()
def demo(
    persona: str = typer.Option("drill_sergeant", "--persona", help="Persona to use"),
    rich_output: bool = typer.Option(
        True, "--rich/--plain", help="Use rich output formatting"
    ),
) -> None:
    """Run a demo of the plugin with sample tests."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=rich_output)
    logger = get_logger(__name__)

    logger.info("Running demo with %s persona", persona)

    try:
        from pathlib import Path

        from pytest_drill_sergeant.core.analysis_pipeline import (
            create_analysis_pipeline,
        )
        from pytest_drill_sergeant.plugin.analysis_storage import get_analysis_storage
        from pytest_drill_sergeant.plugin.personas.manager import get_persona_manager

        typer.echo(f"🎖️  Running demo with {persona} persona...")
        typer.echo("=" * 60)

        # Initialize systems
        storage = get_analysis_storage()
        persona_manager = get_persona_manager()

        # Add analyzers using centralized pipeline
        # Initialize config context for demo
        from pytest_drill_sergeant.core.config_context import initialize_config

        initialize_config()  # Use defaults for demo
        pipeline = create_analysis_pipeline()
        
        # Add all analyzers from pipeline to storage
        for analyzer in pipeline.analyzers:
            storage.add_analyzer(analyzer)

        # Demo with sample files
        sample_files = [
            Path("examples/sample_code/test_with_private_access.py"),
            Path("examples/sample_code/test_clean.py"),
        ]

        total_violations = 0
        total_files = 0

        for sample_file in sample_files:
            if sample_file.exists():
                typer.echo(f"\n🔍 Demo: Analyzing {sample_file.name}")
                findings = storage.analyze_test_file(sample_file)
                total_violations += len(findings)
                total_files += 1

                if findings:
                    typer.echo(f"  Found {len(findings)} violations:")
                    for i, finding in enumerate(findings[:3], 1):  # Show first 3
                        message = persona_manager.on_test_fail(
                            f"demo:{finding.line_number}", finding
                        )
                        typer.echo(f"    {i}. {message}")
                    if len(findings) > 3:
                        typer.echo(f"    ... and {len(findings) - 3} more violations")
                else:
                    success_msg = persona_manager.on_test_pass("demo")
                    typer.echo(f"  ✅ {success_msg}")
            else:
                typer.echo(f"⚠️  Sample file not found: {sample_file}")

        # Demo summary
        typer.echo(f"\n{'='*60}")
        typer.echo("🎖️  DEMO SUMMARY")
        brs_score = max(0, 100 - (total_violations * 15))
        summary_msg = persona_manager.on_summary(
            type(
                "MockMetrics",
                (),
                {
                    "total_tests": total_files,
                    "total_violations": total_violations,
                    "brs_score": brs_score,
                },
            )()
        )
        typer.echo(f"🎖️  {summary_msg}")
        typer.echo(f"📊 Total violations found: {total_violations}")
        typer.echo(f"📁 Files analyzed: {total_files}")

    except Exception as e:
        logger.error("Demo failed: %s", e)
        typer.echo(f"❌ Demo failed: {e}")


@app.command()
def profiles(
    rich_output: bool = typer.Option(
        True, "--rich/--plain", help="Use rich output formatting"
    ),
) -> None:
    """List available profiles and their configurations."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=rich_output)
    logger = get_logger(__name__)

    logger.info("Listing available profiles")

    try:
        from pytest_drill_sergeant.core.config_schema import create_default_config

        config = create_default_config()

        typer.echo("🎯 Available Profiles:")
        typer.echo("=" * 50)

        for profile in ["chill", "standard", "strict"]:
            typer.echo(f"\n📋 {profile.upper()} Profile")
            typer.echo("-" * 20)

            if profile == "chill":
                typer.echo("   🧘 Low-noise, advisory-only")
                typer.echo("   📝 Most rules are INFO level")
                typer.echo("   🎯 Perfect for legacy repos")
            elif profile == "standard":
                typer.echo("   ⚖️  Balanced approach (default)")
                typer.echo("   ⚠️  Most rules are WARNING level")
                typer.echo("   🚀 Good for most projects")
            elif profile == "strict":
                typer.echo("   🔥 High standards, CI-ready")
                typer.echo("   ❌ Most rules are ERROR level")
                typer.echo("   🎖️  Perfect for main branch")

            # Show some example rules for this profile
            typer.echo("\n   Example rules:")
            example_rules = [
                "duplicate_tests",
                "fixture_smells",
                "how_not_what",
                "overmocking",
            ]
            for rule in example_rules:
                if config.is_rule_enabled(rule):
                    severity = config.get_rule_severity(rule)
                    typer.echo(f"     • {rule}: {severity.value}")

        typer.echo("\n💡 Usage Examples:")
        typer.echo("   ds lint tests/ --profile standard")
        typer.echo("   ds lint tests/ --profile strict --fail-on warning")
        typer.echo("   ds lint tests/ --enable duplicate_tests,fixture_smells")
        typer.echo("   ds lint tests/ --treat duplicate_tests:error,overmocking:info")

    except Exception as e:
        logger.error("Failed to list profiles: %s", e)
        typer.echo(f"❌ Failed to list profiles: {e}")


@app.command()
def personas(
    rich_output: bool = typer.Option(
        True, "--rich/--plain", help="Use rich output formatting"
    ),
) -> None:
    """List available personas."""
    # Set up logging based on user preference and context
    setup_logging(use_rich=rich_output)
    logger = get_logger(__name__)

    logger.info("Listing available personas")

    try:
        from pytest_drill_sergeant.plugin.personas.manager import get_persona_manager

        persona_manager = get_persona_manager()
        available_personas = persona_manager.list_personas()

        typer.echo("🎭 Available Personas:")
        typer.echo("=" * 40)

        for persona_name in available_personas:
            try:
                info = persona_manager.get_persona_info(persona_name)
                typer.echo(f"\n🎖️  {info['name']}")
                typer.echo(f"   ID: {info['name']}")
                typer.echo(f"   Description: {info['description']}")

                config = info["config"]
                typer.echo(f"   Style: {config.get('communication_style', 'N/A')}")
                typer.echo(f"   Humor: {config.get('humor_level', 'N/A')}")
                typer.echo(f"   Formality: {config.get('formality_level', 'N/A')}")

            except Exception as e:
                typer.echo(f"\n❌ Error getting info for {persona_name}: {e}")

        typer.echo("\n💡 Use --persona <name> to select a persona")
        typer.echo("   Example: ds lint tests/ --persona drill_sergeant")

    except Exception as e:
        logger.error("Failed to list personas: %s", e)
        typer.echo(f"❌ Failed to list personas: {e}")


def cli() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli()
