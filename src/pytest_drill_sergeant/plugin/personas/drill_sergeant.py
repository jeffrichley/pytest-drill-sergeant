"""Drill Sergeant persona implementation.

This module implements the Drill Sergeant Hartman persona with military-themed
feedback templates inspired by Full Metal Jacket's Gunnery Sergeant Hartman.
"""

from __future__ import annotations

from pytest_drill_sergeant.plugin.personas.models import PersonaConfig
from pytest_drill_sergeant.plugin.personas.strategy import PersonaStrategy


class DrillSergeantPersona(PersonaStrategy):
    """Intense military drill sergeant persona."""

    @property
    def name(self) -> str:
        """Persona name."""
        return "drill_sergeant"

    @property
    def description(self) -> str:
        """Persona description."""
        return "Intense military drill sergeant who demands discipline and precision"

    def _get_persona_config(self) -> PersonaConfig:
        """Get the persona configuration."""
        return PersonaConfig(
            persona_id="drill_sergeant",
            name="Drill Sergeant Hartman",
            description="Intense military drill sergeant who demands discipline and precision",
            personality_traits=[
                "intense", "demanding", "disciplined", "authoritative", "military"
            ],
            communication_style="direct",
            humor_level="high",
            formality_level="casual",
            use_emoji=True,
            use_color=True,
            max_message_length=200,
            feedback_frequency="high",
            enabled=True,
            priority=10
        )

    def _define_templates(self) -> dict[str, list[str]]:
        """Define message templates for the Drill Sergeant persona."""
        return {
            "test_pass": [
                "FINALLY! Test {test_name} passes muster!",
                "OUTSTANDING, RECRUIT! {test_name} shows real discipline!",
                "NOW THAT'S what I call a PROPER test, {test_name}!",
                "Test {test_name} - ACCEPTABLE! You're learning, maggot!",
                "GOOD! {test_name} follows orders like a REAL soldier!",
                "Test {test_name} - APPROVED! That's how you do it, soldier!",
                "EXCELLENT! {test_name} is BATTLE-READY!",
                "Test {test_name} - SATISFACTORY! Keep up the good work!",
            ],
            
            "test_fail": [
                "Test {test_name} is a DISASTER! Fix this MESS before I make you drop and give me twenty!",
                "WHAT IS THIS AMATEUR HOUR?! Test {test_name} needs DISCIPLINE!",
                "Test {test_name} - UNACCEPTABLE! Get your act together, RECRUIT!",
                "Test {test_name} is a MESS! Clean this up, soldier!",
                "PATHETIC! Test {test_name} needs to be FIXED immediately!",
                "Test {test_name} - FAILURE! Report to the barracks for extra training!",
            ],
            
            "test_fail_private_import": [
                "WHAT IS THIS AMATEUR HOUR?! Test {test_name} is importing PRIVATE modules! DO YOU SNEAK INTO THE SERGEANT'S QUARTERS?!",
                "Test {test_name} is snooping around PRIVATE imports! That's NOT how we operate, soldier!",
                "Test {test_name} - UNACCEPTABLE! Stop importing PRIVATE modules, RECRUIT!",
                "WHAT IS THIS?! Test {test_name} is accessing PRIVATE imports! Use the PUBLIC API, maggot!",
            ],
            
            "test_fail_private_attribute": [
                "WHAT IS THIS AMATEUR HOUR?! Test {test_name} is peeking at PRIVATE parts! DO YOU INSPECT THE SERGEANT'S UNDERWEAR?!",
                "Test {test_name} is snooping around PRIVATE attributes! That's NOT how we operate, soldier!",
                "Test {test_name} - UNACCEPTABLE! Stop accessing PRIVATE attributes, RECRUIT!",
                "WHAT IS THIS?! Test {test_name} is touching PRIVATE data! Use the PUBLIC interface, maggot!",
            ],
            
            "test_fail_private_method": [
                "Test {test_name} is calling PRIVATE methods! That's like calling the SERGEANT by his first name!",
                "WHAT IS THIS?! Test {test_name} is invoking PRIVATE methods! Use PUBLIC methods, soldier!",
                "Test {test_name} - UNACCEPTABLE! Stop calling PRIVATE methods, RECRUIT!",
                "Test {test_name} is accessing PRIVATE methods! That's NOT how we operate, maggot!",
            ],
            
            "summary_excellent": [
                "EXCELLENT WORK, RECRUITS! Your test suite is BATTLE-READY! NOW MAINTAIN THIS STANDARD!",
                "OUTSTANDING! BRS {brs_score:.1f} shows your unit is COMBAT-READY!",
                "CHAMPIONSHIP LEVEL! BRS {brs_score:.1f} - you're playing like CHAMPIONS!",
                "BRS {brs_score:.1f} - Your test fleet is sailing smooth seas, Captain!",
                "BRS {brs_score:.1f} - How... remarkably adequate. One might even say... acceptable.",
            ],
            
            "summary_good": [
                "ACCEPTABLE performance! BRS {brs_score:.1f} shows improvement, but we can do BETTER!",
                "Good work, but BRS {brs_score:.1f} means we're not at PEAK performance yet!",
                "GREAT EFFORT! BRS {brs_score:.1f} shows real improvement! Keep pushing!",
                "BRS {brs_score:.1f} - Good sailing, but we can catch more favorable winds!",
                "BRS {brs_score:.1f} - How... pleasantly mediocre. There's room for... improvement.",
            ],
            
            "summary_poor": [
                "PATHETIC! BRS {brs_score:.1f}?! This test suite needs DISCIPLINE! Drop and give me twenty parametrizations!",
                "UNACCEPTABLE! BRS {brs_score:.1f} means this unit is NOT READY FOR COMBAT!",
                "BRS {brs_score:.1f} - every team has room to grow! Let's turn this around!",
                "BRS {brs_score:.1f} - The seas be rough, but every good captain learns to navigate!",
                "BRS {brs_score:.1f} - How... disappointingly predictable. Perhaps some... effort might be in order.",
            ],
            
            "bis_excellent": [
                "Test {test_name} scores {score:.1f} - that's CHAMPIONSHIP material!",
                "Test {test_name} scores {score:.1f} - Smooth sailing on the high seas!",
                "Test {test_name} scores {score:.1f} - How... unexpectedly competent.",
            ],
            
            "bis_good": [
                "Test {test_name} scores {score:.1f} - good effort, let's push for excellence!",
                "Test {test_name} scores {score:.1f} - Good navigation, but we can find better winds!",
                "Test {test_name} scores {score:.1f} - How... adequately average.",
            ],
            
            "bis_poor": [
                "Test {test_name} scores {score:.1f} - every champion started somewhere! Let's improve!",
                "Test {test_name} scores {score:.1f} - Time to chart a new course, matey!",
                "Test {test_name} scores {score:.1f} - How... disappointingly substandard.",
            ],
            
            "brs_excellent": [
                "Battlefield Readiness: {brs_score:.1f}/100 - CHAMPIONSHIP TEAM performance!",
                "Battlefield Readiness: {brs_score:.1f}/100 - Your test fleet is ready for adventure!",
                "Battlefield Readiness: {brs_score:.1f}/100 - How... remarkably satisfactory.",
            ],
            
            "brs_good": [
                "Battlefield Readiness: {brs_score:.1f}/100 - Great effort! We're building something special!",
                "Battlefield Readiness: {brs_score:.1f}/100 - Good sailing, but we can catch better winds!",
                "Battlefield Readiness: {brs_score:.1f}/100 - How... adequately mediocre.",
            ],
            
            "brs_poor": [
                "Battlefield Readiness: {brs_score:.1f}/100 - Every champion team starts somewhere! Let's improve together!",
                "Battlefield Readiness: {brs_score:.1f}/100 - Rough seas ahead, but every good captain learns to navigate!",
                "Battlefield Readiness: {brs_score:.1f}/100 - How... predictably disappointing.",
            ],
        }
