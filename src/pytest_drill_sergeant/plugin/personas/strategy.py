"""Base persona strategy classes for feedback generation."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding, RunMetrics
    from pytest_drill_sergeant.plugin.personas.models import PersonaConfig


class PersonaStrategy(ABC):
    """Base class for all persona implementations using templates."""

    def __init__(self) -> None:
        """Initialize the persona strategy."""
        self.templates = self._define_templates()
        self.config = self._get_persona_config()

    @abstractmethod
    def _define_templates(self) -> dict[str, list[str]]:
        """Define message templates for this persona.

        Returns:
            Dictionary mapping template keys to lists of template strings
        """

    @abstractmethod
    def _get_persona_config(self) -> PersonaConfig:
        """Get the persona configuration.

        Returns:
            PersonaConfig object for this persona
        """

    def get_message(
        self, message_type: str, **context: str | int | float | bool
    ) -> str:
        """Get a formatted message for the given type and context.

        Args:
            message_type: Type of message to generate
            **context: Context variables for template formatting

        Returns:
            Formatted message string
        """
        if message_type not in self.templates:
            return f"Unknown message type: {message_type}"

        templates = self.templates[message_type]
        template = random.choice(templates)

        try:
            return template.format(**context)
        except KeyError as e:
            return f"Template error: missing variable {e}"

    @property
    @abstractmethod
    def name(self) -> str:
        """Persona name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Persona description."""

    def on_test_pass(self, test_name: str, **context: str | int | float | bool) -> str:
        """Generate message for passing test.

        Args:
            test_name: Name of the test that passed
            **context: Additional context variables

        Returns:
            Formatted message for test pass
        """
        return self.get_message("test_pass", test_name=test_name, **context)

    def on_test_fail(
        self, test_name: str, finding: Finding, **context: str | int | float | bool
    ) -> str:
        """Generate message for failing test.

        Args:
            test_name: Name of the test that failed
            finding: Finding that caused the failure
            **context: Additional context variables

        Returns:
            Formatted message for test failure
        """
        # Try to get specific message for the finding type
        finding_type = finding.metadata.get("violation_type", "general")
        specific_message_type = f"test_fail_{finding_type}"

        if specific_message_type in self.templates:
            return self.get_message(
                specific_message_type,
                test_name=test_name,
                finding_message=finding.message,
                **context,
            )

        # Fall back to general test failure message
        return self.get_message(
            "test_fail", test_name=test_name, finding_message=finding.message, **context
        )

    def on_summary(
        self, metrics: RunMetrics, **context: str | int | float | bool
    ) -> str:
        """Generate summary message for test run.

        Args:
            metrics: Test run metrics
            **context: Additional context variables

        Returns:
            Formatted summary message
        """
        # Determine summary type based on BRS score
        if hasattr(metrics, "brs_score") and metrics.brs_score >= 85:
            summary_type = "summary_excellent"
        elif hasattr(metrics, "brs_score") and metrics.brs_score >= 70:
            summary_type = "summary_good"
        else:
            summary_type = "summary_poor"

        return self.get_message(
            summary_type,
            brs_score=getattr(metrics, "brs_score", 0.0),
            total_tests=getattr(metrics, "total_tests", 0),
            **context,
        )

    def on_bis_score(
        self, test_name: str, score: float, **context: str | int | float | bool
    ) -> str:
        """Generate message for BIS score.

        Args:
            test_name: Name of the test
            score: BIS score (0-100)
            **context: Additional context variables

        Returns:
            Formatted BIS score message
        """
        if score >= 85:
            score_type = "bis_excellent"
        elif score >= 70:
            score_type = "bis_good"
        else:
            score_type = "bis_poor"

        return self.get_message(score_type, test_name=test_name, score=score, **context)

    def on_brs_score(self, score: float, **context: str | int | float | bool) -> str:
        """Generate message for BRS score.

        Args:
            score: BRS score (0-100)
            **context: Additional context variables

        Returns:
            Formatted BRS score message
        """
        if score >= 85:
            brs_type = "brs_excellent"
        elif score >= 70:
            brs_type = "brs_good"
        else:
            brs_type = "brs_poor"

        return self.get_message(brs_type, brs_score=score, **context)
