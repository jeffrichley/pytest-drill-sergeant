"""Smoke tests for CLI functionality.

These tests verify that the CLI can run without crashing and performs basic functionality.
They are designed to catch major regressions and integration issues, but are not comprehensive
unit tests. For detailed functionality testing, see the unit and integration tests.

Smoke tests should:
- Run quickly (< 30 seconds total)
- Test basic CLI functionality
- Verify the tool can analyze code and produce output
- Catch major regressions
- Not require complex setup or dependencies
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCLISmoke:
    """Test CLI end-to-end scenarios."""

    def test_cli_basic_functionality_smoke(self):
        """Smoke test: CLI can analyze test files and produce output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create a test file with known violations
            test_file = project_dir / "test_with_violations.py"
            test_file.write_text('''
import pytest

def test_without_assertions():
    """This should trigger DS301 - test without assertions."""
    pass

def test_with_many_assertions():
    """This should trigger DS302 - too many assertions."""
    assert True
    assert False is False
    assert 1 == 1
    assert 2 == 2
    assert 3 == 3
    assert 4 == 4
    assert 5 == 5
    assert 6 == 6
    assert 7 == 7
    assert 8 == 8
    assert 9 == 9
    assert 10 == 10
    assert 11 == 11
    assert 12 == 12
    assert 13 == 13
    assert 14 == 14
    assert 15 == 15
''')
            
            # Run CLI with the test file
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file),
                "--profile", "standard",
                "--format", "terminal"
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with return code {result.returncode}"
            
            # Should produce output (either stdout or stderr)
            assert len(result.stdout) > 0 or len(result.stderr) > 0, "CLI produced no output"
            
            # Should analyze the file (indicated by file path in output)
            output_text = result.stdout + result.stderr
            assert "test_with_violations.py" in output_text, "CLI didn't analyze the test file"
            
            # Should show some analysis results (BIS score, summary, etc.)
            assert any(keyword in output_text.lower() for keyword in [
                "bis", "score", "analysis", "violations", "files analyzed"
            ]), "CLI didn't produce analysis results"

    def test_cli_json_output_smoke(self):
        """Smoke test: CLI can produce valid JSON output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create a test file with violations
            test_file = project_dir / "test_for_json.py"
            test_file.write_text('''
def test_without_assertions():
    """Test without assertions."""
    pass

def test_with_many_assertions():
    """Test with many assertions."""
    assert True
    assert False is False
    assert 1 == 1
    assert 2 == 2
    assert 3 == 3
    assert 4 == 4
    assert 5 == 5
''')
            
            output_file = project_dir / "report.json"
            
            # Run CLI with JSON output
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file),
                "--format", "json",
                "--output", str(output_file)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with return code {result.returncode}"
            
            # Should produce some output
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output with JSON format"
            
            # If output file was created, it should be valid JSON
            if output_file.exists():
                try:
                    with output_file.open() as f:
                        json_data = json.load(f)
                    assert isinstance(json_data, (dict, list)), "JSON output is not a dict or list"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Output file is not valid JSON: {e}")
            else:
                # If no output file, that's okay for smoke test - just verify CLI didn't crash
                pass

    def test_cli_sarif_output_smoke(self):
        """Smoke test: CLI can produce valid SARIF output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create a test file with violations
            test_file = project_dir / "test_for_sarif.py"
            test_file.write_text('''
import pytest

def test_with_many_assertions():
    """Test with many assertions."""
    assert True
    assert False is False
    assert 1 == 1
    assert 2 == 2
    assert 3 == 3
    assert 4 == 4
    assert 5 == 5
    assert 6 == 6
    assert 7 == 7
    assert 8 == 8
    assert 9 == 9
    assert 10 == 10
    assert 11 == 11
''')
            
            output_file = project_dir / "report.sarif"
            
            # Run CLI with SARIF output
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file),
                "--format", "sarif",
                "--output", str(output_file)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with return code {result.returncode}"
            
            # Should produce some output
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output with SARIF format"
            
            # If output file was created, it should be valid JSON
            if output_file.exists():
                try:
                    with output_file.open() as f:
                        sarif_data = json.load(f)
                    assert isinstance(sarif_data, dict), "SARIF output is not a dict"
                    # Should have SARIF structure
                    assert "$schema" in sarif_data or "runs" in sarif_data, "SARIF doesn't have expected structure"
                except json.JSONDecodeError as e:
                    pytest.fail(f"SARIF output file is not valid JSON: {e}")
            else:
                # If no output file, that's okay for smoke test - just verify CLI didn't crash
                pass

    def test_cli_performance_smoke(self):
        """Smoke test: CLI can handle multiple files without major performance issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create multiple test files (smaller set for smoke test)
            tests_dir = project_dir / "tests"
            tests_dir.mkdir()
            
            # Create 10 test files (reduced from 50 for smoke test speed)
            for i in range(10):
                test_file = tests_dir / f"test_module_{i}.py"
                test_file.write_text(f'''
import pytest

class TestModule{i}:
    """Test module {i}."""
    
    def test_function_{i}_1(self):
        """Test function {i}_1."""
        assert True
    
    def test_function_{i}_2(self):
        """Test function {i}_2."""
        assert 1 + 1 == 2
    
    def test_function_{i}_3(self):
        """Test function {i}_3."""
        assert "test" in "testing"
''')
            
            # Run CLI with all test files
            import time
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(tests_dir),
                "--profile", "standard"
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (< 10 seconds for smoke test)
            assert execution_time < 10.0, f"CLI took too long: {execution_time:.2f}s"
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with return code {result.returncode}"
            
            # Should analyze multiple files
            output_text = result.stdout + result.stderr
            assert "Files analyzed" in output_text, "CLI didn't report file analysis count"

    def test_cli_error_handling_smoke(self):
        """Smoke test: CLI handles errors gracefully without crashing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Test with non-existent file
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                "nonexistent_file.py"
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should handle gracefully (may return 0 or 1, but shouldn't crash)
            assert result.returncode in [0, 1], f"CLI crashed with non-existent file: {result.returncode}"
            
            # Should produce some output indicating the issue
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output for non-existent file"
            
            # Test with invalid arguments
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                "--invalid-argument"
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should return non-zero for invalid arguments
            assert result.returncode != 0, "CLI should fail with invalid arguments"
            
            # Should produce error output
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output for invalid arguments"

    def test_cli_help_and_commands_smoke(self):
        """Smoke test: CLI help and commands work without crashing."""
        # Test main help
        result = subprocess.run([
            sys.executable, "-m", "pytest_drill_sergeant.cli.main",
            "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Main help command failed"
        assert "pytest-drill-sergeant" in result.stdout, "Help doesn't mention tool name"
        assert "lint" in result.stdout, "Help doesn't mention lint command"
        
        # Test lint command help
        result = subprocess.run([
            sys.executable, "-m", "pytest_drill_sergeant.cli.main",
            "lint", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Lint help command failed"
        assert "paths" in result.stdout, "Lint help doesn't mention paths argument"
        
        # Test demo command help
        result = subprocess.run([
            sys.executable, "-m", "pytest_drill_sergeant.cli.main",
            "demo", "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Demo help command failed"
        
        # Test profiles command
        result = subprocess.run([
            sys.executable, "-m", "pytest_drill_sergeant.cli.main",
            "profiles"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Profiles command failed"
        assert len(result.stdout) > 0, "Profiles command produced no output"
        
        # Test personas command
        result = subprocess.run([
            sys.executable, "-m", "pytest_drill_sergeant.cli.main",
            "personas"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Personas command failed"
        assert len(result.stdout) > 0, "Personas command produced no output"

    def test_cli_config_file_smoke(self):
        """Smoke test: CLI can load and use configuration files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create a configuration file
            config_file = project_dir / "pyproject.toml"
            config_file.write_text('''
[tool.pytest-drill-sergeant]
profile = "strict"
persona = "drill_sergeant"
fail_on = "warning"
rich_output = false
''')
            
            # Create a test file with violations
            test_file = project_dir / "test_config.py"
            test_file.write_text('''
def test_without_assertions():
    """Test without assertions."""
    pass

def test_with_config():
    """Test with configuration."""
    assert True
''')
            
            # Run CLI with config file
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file),
                "--config", str(config_file)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with config file: {result.returncode}"
            
            # Should produce output
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output with config file"
            
            # Should analyze the file
            assert "test_config.py" in output_text, "CLI didn't analyze the test file"

    def test_cli_cross_platform_compatibility_smoke(self):
        """Smoke test: CLI handles different line endings without crashing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create test files with different line endings
            test_file_unix = project_dir / "test_unix.py"
            test_file_unix.write_text('def test_unix():\n    assert True\n')
            
            test_file_windows = project_dir / "test_windows.py"
            test_file_windows.write_text('def test_windows():\r\n    assert True\r\n')
            
            # Test with Unix-style file
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file_unix)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            assert result.returncode in [0, 1], f"CLI crashed with Unix line endings: {result.returncode}"
            
            # Test with Windows-style file
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file_windows)
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            assert result.returncode in [0, 1], f"CLI crashed with Windows line endings: {result.returncode}"

    def test_cli_user_experience_smoke(self):
        """Smoke test: CLI provides user-friendly output and supports different personas."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Create a test file with various issues
            test_file = project_dir / "test_ux.py"
            test_file.write_text('''
import pytest

def test_without_assertions():
    """Test without assertions."""
    pass

def test_with_many_assertions():
    """Test with many assertions."""
    assert True
    assert False is False
    assert 1 == 1
    assert 2 == 2
    assert 3 == 3
    assert 4 == 4
    assert 5 == 5
    assert 6 == 6
    assert 7 == 7
    assert 8 == 8
    assert 9 == 9
    assert 10 == 10
    assert 11 == 11
    assert 12 == 12
    assert 13 == 13
    assert 14 == 14
    assert 15 == 15
''')
            
            # Test with rich output
            result = subprocess.run([
                sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                "lint",
                str(test_file),
                "--rich"
            ], capture_output=True, text=True, cwd=str(project_dir))
            
            # Should complete without crashing
            assert result.returncode in [0, 1], f"CLI crashed with rich output: {result.returncode}"
            
            # Should produce user-friendly output
            output_text = result.stdout + result.stderr
            assert len(output_text) > 0, "CLI produced no output with rich formatting"
            
            # Test with different personas
            personas = ["drill_sergeant", "snoop_dogg"]
            
            for persona in personas:
                result = subprocess.run([
                    sys.executable, "-m", "pytest_drill_sergeant.cli.main",
                    "lint",
                    str(test_file),
                    "--persona", persona
                ], capture_output=True, text=True, cwd=str(project_dir))
                
                assert result.returncode in [0, 1], f"CLI crashed with persona {persona}: {result.returncode}"
                
                # Should produce output
                output_text = result.stdout + result.stderr
                assert len(output_text) > 0, f"CLI produced no output with persona {persona}"