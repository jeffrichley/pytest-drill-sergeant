# Persona System

## Overview

The persona system provides configurable, humorous feedback to make test quality enforcement engaging and memorable. Each persona has a distinct personality and communication style while delivering the same underlying analysis results.

## Design Pattern

### Template-Based Persona System
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
import random

@dataclass
class MessageTemplate:
    """Template for persona messages with placeholders"""
    templates: List[str]
    severity: str = "info"

    def format(self, **kwargs) -> str:
        """Format template with context variables"""
        template = random.choice(self.templates)
        return template.format(**kwargs)

class PersonaStrategy(ABC):
    """Base class for all persona implementations using templates"""

    def __init__(self):
        self.templates = self._define_templates()

    @abstractmethod
    def _define_templates(self) -> Dict[str, MessageTemplate]:
        """Define message templates for this persona"""
        pass

    def get_message(self, message_type: str, **context) -> str:
        """Get a formatted message for the given type and context"""
        if message_type not in self.templates:
            return f"Unknown message type: {message_type}"

        template = self.templates[message_type]
        return template.format(**context)

    @property
    @abstractmethod
    def name(self) -> str:
        """Persona name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Persona description"""
        pass
```

## Core Personas

### 1. Drill Sergeant Hartman
**Inspiration**: Gunnery Sergeant Hartman from Full Metal Jacket

```python
class DrillSergeantPersona(PersonaStrategy):
    """Intense military drill sergeant persona"""

    @property
    def name(self) -> str:
        return "drill_sergeant"

    @property
    def description(self) -> str:
        return "Intense military drill sergeant who demands discipline and precision"

    def _define_templates(self) -> Dict[str, MessageTemplate]:
        return {
            "test_pass": MessageTemplate([
                "FINALLY! Test {test_name} passes muster!",
                "OUTSTANDING, RECRUIT! {test_name} shows real discipline!",
                "NOW THAT'S what I call a PROPER test, {test_name}!",
                "Test {test_name} - ACCEPTABLE! You're learning, maggot!",
                "GOOD! {test_name} follows orders like a REAL soldier!"
            ]),
            "test_fail": MessageTemplate([
                "Test {test_name} is a DISASTER! Fix this MESS before I make you drop and give me twenty!",
                "WHAT IS THIS AMATEUR HOUR?! Test {test_name} needs DISCIPLINE!",
                "Test {test_name} - UNACCEPTABLE! Get your act together, RECRUIT!"
            ]),
            "private_access": MessageTemplate([
                "WHAT IS THIS AMATEUR HOUR?! Test {test_name} is peeking at PRIVATE parts! DO YOU INSPECT THE SERGEANT'S UNDERWEAR?!",
                "Test {test_name} is snooping around PRIVATE affairs! That's NOT how we operate, soldier!"
            ]),
            "mock_overspec": MessageTemplate([
                "Test {test_name} is a MOCK-UP of incompetence! STOP micromanaging the internals, RECRUIT!",
                "Test {test_name} is over-mocking like a rookie! Focus on the MISSION, not the details!"
            ]),
            "aaa_missing": MessageTemplate([
                "Test {test_name} has NO STRUCTURE! WHERE are your AAA comments, soldier?! ARRANGE, ACT, ASSERT - IN THAT ORDER!",
                "Test {test_name} lacks DISCIPLINE! Show me your AAA structure, maggot!"
            ]),
            "summary_excellent": MessageTemplate([
                "EXCELLENT WORK, RECRUITS! Your test suite is BATTLE-READY! NOW MAINTAIN THIS STANDARD!",
                "OUTSTANDING! BRS {brs_score:.1f} shows your unit is COMBAT-READY!"
            ]),
            "summary_good": MessageTemplate([
                "ACCEPTABLE performance! BRS {brs_score:.1f} shows improvement, but we can do BETTER!",
                "Good work, but BRS {brs_score:.1f} means we're not at PEAK performance yet!"
            ]),
            "summary_poor": MessageTemplate([
                "PATHETIC! BRS {brs_score:.1f}?! This test suite needs DISCIPLINE! Drop and give me twenty parametrizations!",
                "UNACCEPTABLE! BRS {brs_score:.1f} means this unit is NOT READY FOR COMBAT!"
            ])
        }

    def get_test_fail_message(self, test_name: str, finding: Finding) -> str:
        """Get specific failure message based on finding type"""
        if finding.rule_id == "private-access":
            return self.get_message("private_access", test_name=test_name)
        elif finding.rule_id == "mock-overspec":
            return self.get_message("mock_overspec", test_name=test_name)
        elif finding.rule_id == "aaa-missing":
            return self.get_message("aaa_missing", test_name=test_name)
        else:
            return self.get_message("test_fail", test_name=test_name)
```

### 2. Snoop Dogg
**Inspiration**: Laid-back, cool hip-hop style

```python
class SnoopDoggPersona(PersonaStrategy):
    """Chill, laid-back hip-hop persona"""

    @property
    def name(self) -> str:
        return "snoop_dogg"

    @property
    def description(self) -> str:
        return "Chill, laid-back hip-hop persona with smooth delivery"

    def on_test_pass(self, test_name: str, context: TestContext) -> str:
        responses = [
            f"Yo, test {test_name} is lookin' smooth, homie!",
            f"That test {test_name} is straight fire, dawg!",
            f"Test {test_name} be passin' like a boss!",
            f"Yo, {test_name} is keepin' it real!",
            f"Test {test_name} is smooth like butter, my dude!"
        ]
        return random.choice(responses)

    def on_test_fail(self, test_name: str, finding: Finding, context: TestContext) -> str:
        if finding.rule_id == "private-access":
            return f"Yo, test {test_name} be snoopin' around private stuff, that ain't cool, homie!"
        elif finding.rule_id == "mock-overspec":
            return f"Test {test_name} be mockin' too much, dawg. Keep it chill!"
        elif finding.rule_id == "aaa-missing":
            return f"Yo, test {test_name} needs some structure, homie. Arrange, Act, Assert - keep it organized!"
        else:
            return f"Test {test_name} needs some work, my dude. Let's smooth this out!"

    def on_summary(self, metrics: RunMetrics, context: RunContext) -> str:
        if metrics.brs_score >= 85:
            return f"Yo, your test suite is lookin' real nice with a {metrics.brs_score:.1f} BRS score! Keep it smooth!"
        elif metrics.brs_score >= 70:
            return f"Not bad, homie! {metrics.brs_score:.1f} BRS score - we can make it even smoother!"
        else:
            return f"Yo, that {metrics.brs_score:.1f} BRS score needs some work, dawg. Let's get it together!"

    def on_bis_score(self, test_name: str, score: float, grade: str) -> str:
        if score >= 85:
            return f"Test {test_name} is smooth with a {score:.1f} score! Keep it real!"
        elif score >= 70:
            return f"Test {test_name} is lookin' good with {score:.1f}, but we can make it smoother!"
        else:
            return f"Test {test_name} needs some work with that {score:.1f} score, homie!"

    def on_brs_score(self, score: float, grade: str, components: Dict[str, float]) -> str:
        if score >= 85:
            return f"Battlefield Readiness: {score:.1f}/100 - Yo, your test suite is straight fire!"
        elif score >= 70:
            return f"Battlefield Readiness: {score:.1f}/100 - Lookin' good, but we can smooth it out more!"
        else:
            return f"Battlefield Readiness: {score:.1f}/100 - Yo, we need to step up this game, homie!"
```

### 3. Motivational Coach
**Inspiration**: Enthusiastic sports coach

```python
class MotivationalCoachPersona(PersonaStrategy):
    """Enthusiastic, encouraging sports coach persona"""

    @property
    def name(self) -> str:
        return "motivational_coach"

    @property
    def description(self) -> str:
        return "Enthusiastic sports coach who encourages and motivates"

    def on_test_pass(self, test_name: str, context: TestContext) -> str:
        responses = [
            f"YES! Test {test_name} is a WINNER! That's what I'm talking about!",
            f"FANTASTIC! Test {test_name} shows real TEAM SPIRIT!",
            f"OUTSTANDING performance from test {test_name}! You're on FIRE!",
            f"Test {test_name} - NOW THAT'S how you play the game!",
            f"BRILLIANT! Test {test_name} is giving 110%!"
        ]
        return random.choice(responses)

    def on_test_fail(self, test_name: str, finding: Finding, context: TestContext) -> str:
        if finding.rule_id == "private-access":
            return f"Hey test {test_name}, let's focus on the PUBLIC game plan, not the private plays!"
        elif finding.rule_id == "mock-overspec":
            return f"Test {test_name}, we need to trust our teammates more and stop micromanaging!"
        elif finding.rule_id == "aaa-missing":
            return f"Test {test_name}, remember our game plan: ARRANGE the play, ACT on it, and ASSERT the result!"
        else:
            return f"Test {test_name}, every champion faces challenges. Let's work on this together!"

    def on_summary(self, metrics: RunMetrics, context: RunContext) -> str:
        if metrics.brs_score >= 85:
            return f"CHAMPIONSHIP LEVEL! BRS {metrics.brs_score:.1f} - you're playing like CHAMPIONS!"
        elif metrics.brs_score >= 70:
            return f"GREAT EFFORT! BRS {metrics.brs_score:.1f} shows real improvement! Keep pushing!"
        else:
            return f"BRS {metrics.brs_score:.1f} - every team has room to grow! Let's turn this around!"

    def on_bis_score(self, test_name: str, score: float, grade: str) -> str:
        if score >= 85:
            return f"Test {test_name} scores {score:.1f} - that's CHAMPIONSHIP material!"
        elif score >= 70:
            return f"Test {test_name} scores {score:.1f} - good effort, let's push for excellence!"
        else:
            return f"Test {test_name} scores {score:.1f} - every champion started somewhere! Let's improve!"

    def on_brs_score(self, score: float, grade: str, components: Dict[str, float]) -> str:
        if score >= 85:
            return f"Battlefield Readiness: {score:.1f}/100 - CHAMPIONSHIP TEAM performance!"
        elif score >= 70:
            return f"Battlefield Readiness: {score:.1f}/100 - Great effort! We're building something special!"
        else:
            return f"Battlefield Readiness: {score:.1f}/100 - Every champion team starts somewhere! Let's improve together!"
```

### 4. Sarcastic Butler
**Inspiration**: British butler with dry wit

```python
class SarcasticButlerPersona(PersonaStrategy):
    """Dry, sarcastic British butler persona"""

    @property
    def name(self) -> str:
        return "sarcastic_butler"

    @property
    def description(self) -> str:
        return "Dry, sarcastic British butler with impeccable manners and cutting wit"

    def on_test_pass(self, test_name: str, context: TestContext) -> str:
        responses = [
            f"How... adequate. Test {test_name} has managed to pass.",
            f"Well, well. Test {test_name} appears to be functioning. How... unexpected.",
            f"Test {test_name} has deigned to pass. How perfectly... satisfactory.",
            f"Ah, test {test_name}. How delightfully... competent.",
            f"Test {test_name} passes. How... refreshingly uneventful."
        ]
        return random.choice(responses)

    def on_test_fail(self, test_name: str, finding: Finding, context: TestContext) -> str:
        if finding.rule_id == "private-access":
            return f"Test {test_name} appears to be... rummaging through private affairs. How... gauche."
        elif finding.rule_id == "mock-overspec":
            return f"Test {test_name} seems to have developed an unhealthy obsession with mockery. How... tiresome."
        elif finding.rule_id == "aaa-missing":
            return f"Test {test_name} lacks the most basic organizational structure. How... predictable."
        else:
            return f"Test {test_name} has encountered a... difficulty. How... unfortunate."

    def on_summary(self, metrics: RunMetrics, context: RunContext) -> str:
        if metrics.brs_score >= 85:
            return f"BRS {metrics.brs_score:.1f} - How... remarkably adequate. One might even say... acceptable."
        elif metrics.brs_score >= 70:
            return f"BRS {metrics.brs_score:.1f} - How... pleasantly mediocre. There's room for... improvement."
        else:
            return f"BRS {metrics.brs_score:.1f} - How... disappointingly predictable. Perhaps some... effort might be in order."

    def on_bis_score(self, test_name: str, score: float, grade: str) -> str:
        if score >= 85:
            return f"Test {test_name} scores {score:.1f} - How... unexpectedly competent."
        elif score >= 70:
            return f"Test {test_name} scores {score:.1f} - How... adequately average."
        else:
            return f"Test {test_name} scores {score:.1f} - How... disappointingly substandard."

    def on_brs_score(self, score: float, grade: str, components: Dict[str, float]) -> str:
        if score >= 85:
            return f"Battlefield Readiness: {score:.1f}/100 - How... remarkably satisfactory."
        elif score >= 70:
            return f"Battlefield Readiness: {score:.1f}/100 - How... adequately mediocre."
        else:
            return f"Battlefield Readiness: {score:.1f}/100 - How... predictably disappointing."
```

### 5. Pirate
**Inspiration**: Swashbuckling pirate with nautical terminology

```python
class PiratePersona(PersonaStrategy):
    """Swashbuckling pirate persona with nautical terminology"""

    @property
    def name(self) -> str:
        return "pirate"

    @property
    def description(self) -> str:
        return "Swashbuckling pirate with nautical terminology and adventurous spirit"

    def on_test_pass(self, test_name: str, context: TestContext) -> str:
        responses = [
            f"Ahoy! Test {test_name} has sailed through smooth waters!",
            f"Shiver me timbers! Test {test_name} is shipshape and Bristol fashion!",
            f"Test {test_name} has weathered the storm like a true sea dog!",
            f"Avast ye! Test {test_name} is sailing true to course!",
            f"Test {test_name} has found the treasure of passing tests!"
        ]
        return random.choice(responses)

    def on_test_fail(self, test_name: str, finding: Finding, context: TestContext) -> str:
        if finding.rule_id == "private-access":
            return f"Arr! Test {test_name} be snoopin' in private quarters! That's not the pirate way!"
        elif finding.rule_id == "mock-overspec":
            return f"Test {test_name} be mockin' too much! A true pirate faces the real sea!"
        elif finding.rule_id == "aaa-missing":
            return f"Test {test_name} needs to chart a proper course: Arrange, Act, Assert!"
        else:
            return f"Test {test_name} has run aground! Time to patch the ship and set sail again!"

    def on_summary(self, metrics: RunMetrics, context: RunContext) -> str:
        if metrics.brs_score >= 85:
            return f"BRS {metrics.brs_score:.1f} - Your test fleet is sailing smooth seas, Captain!"
        elif metrics.brs_score >= 70:
            return f"BRS {metrics.brs_score:.1f} - Good sailing, but we can catch more favorable winds!"
        else:
            return f"BRS {metrics.brs_score:.1f} - The seas be rough, but every good captain learns to navigate!"

    def on_bis_score(self, test_name: str, score: float, grade: str) -> str:
        if score >= 85:
            return f"Test {test_name} scores {score:.1f} - Smooth sailing on the high seas!"
        elif score >= 70:
            return f"Test {test_name} scores {score:.1f} - Good navigation, but we can find better winds!"
        else:
            return f"Test {test_name} scores {score:.1f} - Time to chart a new course, matey!"

    def on_brs_score(self, score: float, grade: str, components: Dict[str, float]) -> str:
        if score >= 85:
            return f"Battlefield Readiness: {score:.1f}/100 - Your test fleet is ready for adventure!"
        elif score >= 70:
            return f"Battlefield Readiness: {score:.1f}/100 - Good sailing, but we can catch better winds!"
        else:
            return f"Battlefield Readiness: {score:.1f}/100 - Rough seas ahead, but every good captain learns to navigate!"
```

## Persona Manager

### Configuration and Selection
```python
class PersonaManager:
    """Manages persona selection and configuration"""

    def __init__(self):
        self.personas: Dict[str, PersonaStrategy] = {
            "drill_sergeant": DrillSergeantPersona(),
            "snoop_dogg": SnoopDoggPersona(),
            "motivational_coach": MotivationalCoachPersona(),
            "sarcastic_butler": SarcasticButlerPersona(),
            "pirate": PiratePersona(),
        }
        self.current_persona: Optional[PersonaStrategy] = None

    def set_persona(self, persona_name: str) -> None:
        """Set the active persona"""
        if persona_name in self.personas:
            self.current_persona = self.personas[persona_name]
        else:
            raise ValueError(f"Unknown persona: {persona_name}")

    def get_current_persona(self) -> PersonaStrategy:
        """Get the current active persona"""
        if self.current_persona is None:
            # Default to drill sergeant
            self.current_persona = self.personas["drill_sergeant"]
        return self.current_persona

    def list_personas(self) -> List[Dict[str, str]]:
        """List available personas"""
        return [
            {"name": name, "description": persona.description}
            for name, persona in self.personas.items()
        ]

    def add_custom_persona(self, name: str, persona: PersonaStrategy) -> None:
        """Add a custom persona"""
        self.personas[name] = persona
```

### Integration with Pytest Hooks
```python
class PersonaIntegration:
    """Integration of personas with pytest hooks"""

    def __init__(self, persona_manager: PersonaManager):
        self.persona_manager = persona_manager

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Inject persona feedback into test reports"""
        if report.when == "call":
            persona = self.persona_manager.get_current_persona()

            if report.outcome == "passed":
                feedback = persona.on_test_pass(report.nodeid, self._get_test_context(report))
            else:
                findings = self._get_test_findings(report)
                feedback = persona.on_test_fail(report.nodeid, findings[0], self._get_test_context(report))

            # Add feedback to report
            report.sections.append(("persona_feedback", feedback))

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config) -> None:
        """Add persona summary to terminal output"""
        persona = self.persona_manager.get_current_persona()
        metrics = self._get_run_metrics(config)

        summary = persona.on_summary(metrics, self._get_run_context(config))

        terminalreporter._tw.write(f"\n{persona.name.upper()} REPORT:\n")
        terminalreporter._tw.write(f"{summary}\n")
```

## Configuration

### Persona Selection
```toml
[tool.pytest_drill_sergeant]
persona = "drill_sergeant"  # Default persona

[tool.pytest_drill_sergeant.personas]
# Enable specific personas
enabled = ["drill_sergeant", "snoop_dogg", "motivational_coach"]

# Custom persona settings
drill_sergeant.intensity = "high"
snoop_dogg.coolness_factor = "maximum"
motivational_coach.enthusiasm = "extreme"
```

### CLI Persona Selection
```bash
# Use specific persona
pytest --persona=snoop_dogg

# List available personas
pytest --list-personas

# Use custom persona
pytest --persona=my_custom_persona
```

## Extensibility

### Custom Persona Creation
```python
class MyCustomPersona(PersonaStrategy):
    """Custom persona implementation"""

    @property
    def name(self) -> str:
        return "my_custom"

    @property
    def description(self) -> str:
        return "My custom persona description"

    def on_test_pass(self, test_name: str, context: TestContext) -> str:
        return f"Custom feedback for passing test {test_name}"

    # Implement other abstract methods...
```

### Persona Plugin System
```python
class PersonaPlugin:
    """Plugin system for custom personas"""

    def __init__(self):
        self.registered_personas: Dict[str, Type[PersonaStrategy]] = {}

    def register_persona(self, name: str, persona_class: Type[PersonaStrategy]) -> None:
        """Register a custom persona"""
        self.registered_personas[name] = persona_class

    def create_persona(self, name: str) -> PersonaStrategy:
        """Create an instance of a registered persona"""
        if name in self.registered_personas:
            return self.registered_personas[name]()
        raise ValueError(f"Unknown persona: {name}")
```
