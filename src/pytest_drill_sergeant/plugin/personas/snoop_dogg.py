"""Snoop Dogg persona for testing purposes."""

from __future__ import annotations

from pytest_drill_sergeant.plugin.personas.models import PersonaConfig
from pytest_drill_sergeant.plugin.personas.strategy import PersonaStrategy


class SnoopDoggPersona(PersonaStrategy):
    """Snoop Dogg persona for testing purposes."""

    @property
    def name(self) -> str:
        """Persona name."""
        return "snoop_dogg"

    @property
    def description(self) -> str:
        """Persona description."""
        return "West Coast rapper persona for testing purposes"

    def _get_persona_config(self) -> PersonaConfig:
        """Get the persona configuration."""
        return PersonaConfig(
            persona_id="snoop_dogg",
            name="Snoop Dogg",
            description="West Coast rapper persona for testing purposes",
            personality_traits=[
                "cool",
                "laid-back",
                "street-smart",
                "rhythmic",
                "test-friendly",
            ],
            communication_style="casual",
            humor_level="medium",
            formality_level="very_casual",
            use_emoji=True,
            use_color=True,
            max_message_length=150,
            feedback_frequency="medium",
            enabled=True,
            priority=5,
        )

    def _define_templates(self) -> dict[str, list[str]]:
        """Define message templates for this persona."""
        return {
            "test_pass": [
                "Fo' shizzle, {test_name} is straight fire! 🔥",
                "That's what I'm talkin' about, {test_name}! Keep it real!",
                "Yo, {test_name} is on point! That's how we do it!",
            ],
            "test_fail": [
                "Yo, {test_name} needs some work, homie. Check out these violations!",
                "Ain't no good, {test_name}. You gotta step up your game!",
                "That's not how we roll, {test_name}. Fix these issues!",
            ],
            "summary": [
                "BRS {brs_score:.1f} - That's what I'm talkin' about!",
                "BRS {brs_score:.1f} - Keep it real, homie!",
                "BRS {brs_score:.1f} - That's the way to do it!",
            ],
            "bis_score": [
                "BIS {score:.1f} - Keep it real!",
                "BIS {score:.1f} - That's how we do it!",
                "BIS {score:.1f} - Straight fire!",
            ],
            "brs_score": [
                "BRS {score:.1f} - That's the way to do it!",
                "BRS {score:.1f} - Keep it real, homie!",
                "BRS {score:.1f} - That's what I'm talkin' about!",
            ],
        }
