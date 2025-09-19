"""Tests for the Drill Sergeant Persona."""

from __future__ import annotations

from pathlib import Path

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.plugin.personas.drill_sergeant import DrillSergeantPersona


class TestDrillSergeantPersona:
    """Test the Drill Sergeant Persona functionality."""

    def test_init(self) -> None:
        """Test persona initialization."""
        persona = DrillSergeantPersona()
        assert persona.name == "drill_sergeant"
        assert "military" in persona.description.lower()
        assert persona.config.persona_id == "drill_sergeant"

    def test_persona_config(self) -> None:
        """Test persona configuration."""
        persona = DrillSergeantPersona()
        config = persona.config

        assert config.name == "Drill Sergeant Hartman"
        assert "intense" in config.personality_traits
        assert "demanding" in config.personality_traits
        assert config.communication_style == "direct"
        assert config.humor_level == "high"
        assert config.use_emoji is True
        assert config.use_color is True
        assert config.enabled is True
        assert config.priority == 10

    def test_test_pass_message(self) -> None:
        """Test test pass message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_test_pass("test_something")

        assert "test_something" in message
        # Check for any positive military-themed words
        assert any(
            word in message.upper()
            for word in [
                "FINALLY",
                "OUTSTANDING",
                "GOOD",
                "EXCELLENT",
                "PROPER",
                "ACCEPTABLE",
                "REAL",
                "SOLDIER",
                "BATTLE-READY",
                "APPROVED",
                "SATISFACTORY",
            ]
        )
        assert len(message) <= persona.config.max_message_length

    def test_test_fail_message_general(self) -> None:
        """Test general test fail message generation."""
        persona = DrillSergeantPersona()

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Some violation",
            file_path=Path("test.py"),
            line_number=1,
        )

        message = persona.on_test_fail("test_something", finding)

        assert "test_something" in message
        # Check for any negative military-themed words
        assert any(
            word in message.upper()
            for word in [
                "DISASTER",
                "AMATEUR",
                "UNACCEPTABLE",
                "PATHETIC",
                "MESS",
                "FAILURE",
                "BARRACKS",
                "TRAINING",
                "DISCIPLINE",
                "RECRUIT",
            ]
        )
        assert len(message) <= persona.config.max_message_length

    def test_test_fail_message_private_import(self) -> None:
        """Test private import violation message generation."""
        persona = DrillSergeantPersona()

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Importing private module: myapp._internal",
            file_path=Path("test.py"),
            line_number=1,
            metadata={"violation_type": "private_import"},
        )

        message = persona.on_test_fail("test_something", finding)

        assert "test_something" in message
        assert any(
            word in message.upper()
            for word in ["PRIVATE", "IMPORT", "SERGEANT", "QUARTERS"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_test_fail_message_private_attribute(self) -> None:
        """Test private attribute violation message generation."""
        persona = DrillSergeantPersona()

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Accessing private attribute: _private_attr",
            file_path=Path("test.py"),
            line_number=1,
            metadata={"violation_type": "private_attribute"},
        )

        message = persona.on_test_fail("test_something", finding)

        assert "test_something" in message
        assert any(
            word in message.upper()
            for word in ["PRIVATE", "ATTRIBUTE", "UNDERWEAR", "SERGEANT"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_test_fail_message_private_method(self) -> None:
        """Test private method violation message generation."""
        persona = DrillSergeantPersona()

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Calling private method: _private_method",
            file_path=Path("test.py"),
            line_number=1,
            metadata={"violation_type": "private_method"},
        )

        message = persona.on_test_fail("test_something", finding)

        assert "test_something" in message
        assert any(
            word in message.upper()
            for word in ["PRIVATE", "METHOD", "SERGEANT", "FIRST NAME"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_summary_excellent(self) -> None:
        """Test excellent summary message generation."""
        persona = DrillSergeantPersona()

        # Mock RunMetrics with high BRS score
        class MockMetrics:
            brs_score = 90.0
            total_tests = 100

        message = persona.on_summary(MockMetrics())

        assert any(
            word in message.upper()
            for word in [
                "EXCELLENT",
                "OUTSTANDING",
                "CHAMPIONSHIP",
                "BATTLE-READY",
                "ADEQUATE",
                "ACCEPTABLE",
                "REMARKABLY",
            ]
        )
        # Some templates include the score, others don't - both are valid
        assert len(message) <= persona.config.max_message_length

    def test_summary_good(self) -> None:
        """Test good summary message generation."""
        persona = DrillSergeantPersona()

        # Mock RunMetrics with medium BRS score
        class MockMetrics:
            brs_score = 75.0
            total_tests = 100

        message = persona.on_summary(MockMetrics())

        assert any(
            word in message.upper()
            for word in ["ACCEPTABLE", "GOOD", "IMPROVEMENT", "BETTER"]
        )
        assert "75.0" in message
        assert len(message) <= persona.config.max_message_length

    def test_summary_poor(self) -> None:
        """Test poor summary message generation."""
        persona = DrillSergeantPersona()

        # Mock RunMetrics with low BRS score
        class MockMetrics:
            brs_score = 45.0
            total_tests = 100

        message = persona.on_summary(MockMetrics())

        assert any(
            word in message.upper()
            for word in [
                "PATHETIC",
                "UNACCEPTABLE",
                "DISCIPLINE",
                "COMBAT",
                "GROW",
                "TURN",
                "NAVIGATE",
                "PREDICTABLE",
            ]
        )
        # Some templates include the score, others don't - both are valid
        assert len(message) <= persona.config.max_message_length

    def test_bis_score_excellent(self) -> None:
        """Test excellent BIS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_bis_score("test_something", 90.0)

        assert "test_something" in message
        assert "90.0" in message
        assert any(
            word in message.upper() for word in ["CHAMPIONSHIP", "SMOOTH", "COMPETENT"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_bis_score_good(self) -> None:
        """Test good BIS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_bis_score("test_something", 75.0)

        assert "test_something" in message
        assert "75.0" in message
        assert any(
            word in message.upper()
            for word in ["GOOD", "IMPROVEMENT", "EXCELLENCE", "AVERAGE"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_bis_score_poor(self) -> None:
        """Test poor BIS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_bis_score("test_something", 45.0)

        assert "test_something" in message
        assert "45.0" in message
        assert any(
            word in message.upper()
            for word in ["CHAMPION", "IMPROVE", "COURSE", "SUBSTANDARD"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_brs_score_excellent(self) -> None:
        """Test excellent BRS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_brs_score(90.0)

        assert "90.0" in message
        assert any(
            word in message.upper()
            for word in ["CHAMPIONSHIP", "FLEET", "SATISFACTORY"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_brs_score_good(self) -> None:
        """Test good BRS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_brs_score(75.0)

        assert "75.0" in message
        assert any(word in message.upper() for word in ["GREAT", "SAILING", "MEDIOCRE"])
        assert len(message) <= persona.config.max_message_length

    def test_brs_score_poor(self) -> None:
        """Test poor BRS score message generation."""
        persona = DrillSergeantPersona()

        message = persona.on_brs_score(45.0)

        assert "45.0" in message
        assert any(
            word in message.upper()
            for word in ["CHAMPION", "NAVIGATE", "DISAPPOINTING"]
        )
        assert len(message) <= persona.config.max_message_length

    def test_get_message_unknown_type(self) -> None:
        """Test handling of unknown message types."""
        persona = DrillSergeantPersona()

        message = persona.get_message("unknown_type", test_name="test_something")

        assert message == "Unknown message type: unknown_type"

    def test_get_message_missing_variable(self) -> None:
        """Test handling of missing template variables."""
        persona = DrillSergeantPersona()

        # This should not raise an exception, but return an error message
        message = persona.get_message("test_pass")  # Missing test_name variable

        assert "Template error" in message

    def test_message_randomization(self) -> None:
        """Test that messages are randomized (multiple calls return different messages)."""
        persona = DrillSergeantPersona()

        messages = set()
        for _ in range(10):
            message = persona.on_test_pass("test_something")
            messages.add(message)

        # Should have multiple different messages (not all the same)
        assert len(messages) > 1

    def test_all_templates_have_required_variables(self) -> None:
        """Test that all templates can be formatted with their required variables."""
        persona = DrillSergeantPersona()

        # Test each template type with appropriate variables
        test_cases = [
            ("test_pass", {"test_name": "test_something"}),
            (
                "test_fail",
                {"test_name": "test_something", "finding_message": "Some error"},
            ),
            (
                "test_fail_private_import",
                {"test_name": "test_something", "finding_message": "Import error"},
            ),
            (
                "test_fail_private_attribute",
                {"test_name": "test_something", "finding_message": "Attribute error"},
            ),
            (
                "test_fail_private_method",
                {"test_name": "test_something", "finding_message": "Method error"},
            ),
            ("summary_excellent", {"brs_score": 90.0}),
            ("summary_good", {"brs_score": 75.0}),
            ("summary_poor", {"brs_score": 45.0}),
            ("bis_excellent", {"test_name": "test_something", "score": 90.0}),
            ("bis_good", {"test_name": "test_something", "score": 75.0}),
            ("bis_poor", {"test_name": "test_something", "score": 45.0}),
            ("brs_excellent", {"brs_score": 90.0}),
            ("brs_good", {"brs_score": 75.0}),
            ("brs_poor", {"brs_score": 45.0}),
        ]

        for template_type, variables in test_cases:
            message = persona.get_message(template_type, **variables)
            assert "Template error" not in message
            assert len(message) > 0

    def test_message_length_constraints(self) -> None:
        """Test that all messages respect length constraints."""
        persona = DrillSergeantPersona()

        # Test various message types
        messages = [
            persona.on_test_pass("test_something"),
            persona.on_test_fail(
                "test_something",
                Finding(
                    code="DS201",
                    name="private_access",
                    severity=Severity.WARNING,
                    message="Some violation",
                    file_path=Path("test.py"),
                    line_number=1,
                ),
            ),
            persona.on_bis_score("test_something", 75.0),
            persona.on_brs_score(75.0),
        ]

        for message in messages:
            assert len(message) <= persona.config.max_message_length
