"""Persona manager for handling persona selection and configuration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.config_manager import get_config
from pytest_drill_sergeant.plugin.personas.drill_sergeant import DrillSergeantPersona
from pytest_drill_sergeant.plugin.personas.snoop_dogg import SnoopDoggPersona
from pytest_drill_sergeant.plugin.personas.strategy import PersonaStrategy

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding, RunMetrics

logger = logging.getLogger(__name__)


class PersonaManager:
    """Manages persona selection and configuration."""

    def __init__(self) -> None:
        """Initialize the persona manager."""
        self._personas: dict[str, PersonaStrategy] = {}
        self._current_persona: PersonaStrategy | None = None
        self._initialize_personas()

    def _initialize_personas(self) -> None:
        """Initialize available personas."""
        # Register built-in personas
        drill_sergeant = DrillSergeantPersona()
        self._personas[drill_sergeant.name] = drill_sergeant

        snoop_dogg = SnoopDoggPersona()
        self._personas[snoop_dogg.name] = snoop_dogg

        logger.debug("Registered persona: %s", drill_sergeant.name)
        logger.debug("Registered persona: %s", snoop_dogg.name)

    def get_persona(
        self, name: str | None = None, fallback_on_missing: bool = True
    ) -> PersonaStrategy:
        """Get a persona by name or the configured default.

        Args:
            name: Persona name to get. If None, uses configured default.
            fallback_on_missing: If True, fall back to drill_sergeant when persona not found.
                                If False, raise ValueError for missing personas.

        Returns:
            PersonaStrategy instance

        Raises:
            ValueError: If persona not found and fallback_on_missing is False
        """
        if name is None:
            name = self._get_default_persona_name()
            # For config-driven selection, always allow fallback
            fallback_on_missing = True

        if name not in self._personas:
            available = ", ".join(self._personas.keys())
            if fallback_on_missing:
                logger.warning(
                    "Persona '%s' not found. Available: %s. Using 'drill_sergeant' as fallback.", name, available
                )
                # Fall back to drill_sergeant if requested persona not found
                name = "drill_sergeant"
                if name not in self._personas:
                    raise ValueError(
                        f"Default persona '{name}' not found. Available: {available}"
                    )
            else:
                raise ValueError(f"Persona '{name}' not found. Available: {available}")

        return self._personas[name]

    def _get_default_persona_name(self) -> str:
        """Get the default persona name from configuration."""
        try:
            config = get_config()
            return getattr(config, "persona", "drill_sergeant")
        except Exception:
            logger.debug("Could not get persona from config, using default")
            return "drill_sergeant"

    def list_personas(self) -> list[str]:
        """List available persona names.

        Returns:
            List of persona names
        """
        return list(self._personas.keys())

    def get_persona_info(self, name: str) -> dict[str, str]:
        """Get information about a persona.

        Args:
            name: Persona name

        Returns:
            Dictionary with persona information

        Raises:
            ValueError: If persona not found
        """
        persona = self.get_persona(name)
        return {
            "name": persona.name,
            "description": persona.description,
            "config": persona.config.model_dump(),
        }

    def on_test_pass(self, test_name: str, **context: str | int | float | bool) -> str:
        """Generate test pass message using current persona.

        Args:
            test_name: Name of the test that passed
            **context: Additional context variables

        Returns:
            Formatted message for test pass
        """
        persona = self.get_persona()
        return persona.on_test_pass(test_name, **context)

    def on_test_fail(
        self, test_name: str, finding: Finding, **context: str | int | float | bool
    ) -> str:
        """Generate test fail message using current persona.

        Args:
            test_name: Name of the test that failed
            finding: Finding that caused the failure
            **context: Additional context variables

        Returns:
            Formatted message for test failure
        """
        persona = self.get_persona()
        return persona.on_test_fail(test_name, finding, **context)

    def on_summary(
        self, metrics: RunMetrics, **context: str | int | float | bool
    ) -> str:
        """Generate summary message using current persona.

        Args:
            metrics: Test run metrics
            **context: Additional context variables

        Returns:
            Formatted summary message
        """
        persona = self.get_persona()
        return persona.on_summary(metrics, **context)

    def on_bis_score(
        self, test_name: str, score: float, **context: str | int | float | bool
    ) -> str:
        """Generate BIS score message using current persona.

        Args:
            test_name: Name of the test
            score: BIS score (0-100)
            **context: Additional context variables

        Returns:
            Formatted BIS score message
        """
        persona = self.get_persona()
        return persona.on_bis_score(test_name, score, **context)

    def on_brs_score(self, score: float, **context: str | int | float | bool) -> str:
        """Generate BRS score message using current persona.

        Args:
            score: BRS score (0-100)
            **context: Additional context variables

        Returns:
            Formatted BRS score message
        """
        persona = self.get_persona()
        return persona.on_brs_score(score, **context)


# Global persona manager instance
_persona_manager: PersonaManager | None = None


def get_persona_manager() -> PersonaManager:
    """Get the global persona manager instance.

    Returns:
        PersonaManager instance
    """
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager
