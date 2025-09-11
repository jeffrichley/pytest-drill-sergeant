"""Unit tests for the pytest_options module."""

from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.pytest_options import pytest_addoption


@pytest.mark.unit
class TestPytestOptions:
    """Test the pytest_options module."""

    def test_pytest_addoption_function_exists(self) -> None:
        """Test that pytest_addoption function exists and is callable."""
        # Arrange - No setup needed for function existence test

        # Act - Access the pytest_addoption function

        # Assert - Verify function exists and is callable
        assert pytest_addoption is not None
        assert callable(pytest_addoption)

    def test_pytest_addoption_can_be_called(self) -> None:
        """Test that pytest_addoption can be called without errors."""
        # Arrange - Set up mock parser for pytest_addoption
        mock_parser = Mock()

        # Act - Call pytest_addoption with mock parser
        pytest_addoption(mock_parser)

        # Assert - Verify function was called without errors
        # The function should have added options to the parser
        assert True  # If we get here, the function executed without errors

    def test_pytest_addoption_adds_expected_options(self) -> None:
        """Test that pytest_addoption adds expected ini options."""
        # Arrange - Set up mock parser to track addini calls
        mock_parser = Mock()
        addini_calls = []

        def track_addini(*args, **kwargs):
            addini_calls.append((args, kwargs))

        mock_parser.addini.side_effect = track_addini

        # Act - Call pytest_addoption with mock parser
        pytest_addoption(mock_parser)

        # Assert - Verify that addini was called multiple times
        assert (
            len(addini_calls) > 0
        ), "pytest_addoption should add at least one ini option"

        # Verify that some expected options were added
        option_names = [call[0][0] for call in addini_calls if call[0]]
        expected_options = [
            "drill_sergeant_enabled",
            "drill_sergeant_enforce_markers",
            "drill_sergeant_enforce_aaa",
            "drill_sergeant_enforce_file_length",
            "drill_sergeant_auto_detect_markers",
            "drill_sergeant_min_description_length",
            "drill_sergeant_max_file_length",
        ]

        for expected_option in expected_options:
            assert (
                expected_option in option_names
            ), f"Expected option {expected_option} not found in added options"

    def test_pytest_addoption_options_have_help_text(self) -> None:
        """Test that pytest_addoption options have help text."""
        # Arrange - Set up mock parser to track addini calls
        mock_parser = Mock()
        addini_calls = []

        def track_addini(*args, **kwargs):
            addini_calls.append((args, kwargs))

        mock_parser.addini.side_effect = track_addini

        # Act - Call pytest_addoption with mock parser
        pytest_addoption(mock_parser)

        # Assert - Verify that options have help text
        for call in addini_calls:
            args, kwargs = call
            if len(args) >= 2:
                # Check if help is provided as keyword argument
                has_help = "help" in kwargs
                assert (
                    has_help
                ), f"Option {args[0] if args else 'unknown'} should have help text"
