#!/usr/bin/env python3
"""Debug file discovery logic."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pytest_drill_sergeant.core.file_discovery import FileDiscoveryConfig

def main():
    project_root = Path("/Users/jeffrichley/workspace/tools/pytest-drill-sergeant")
    
    # Create file discovery config directly
    file_discovery_config = FileDiscoveryConfig(project_root)
    
    # Test files
    test_file = project_root / "tests/unit/test_coverage_analysis.py"
    venv_file = project_root / ".venv/bin/python"
    
    print(f"Project root: {project_root}")
    print(f"Test file: {test_file}")
    print(f"Venv file: {venv_file}")
    print()
    
    # Debug the patterns
    print("\nInclude patterns:")
    for pattern in file_discovery_config.include_patterns:
        print(f"  {pattern}")
    
    print("\nExclude patterns:")
    for pattern in file_discovery_config.exclude_patterns:
        print(f"  {pattern}")
    
    # Test individual pattern matching
    print("\nTesting pattern matching:")
    for pattern in file_discovery_config.exclude_patterns:
        test_match = pattern.matches(test_file, project_root)
        venv_match = pattern.matches(venv_file, project_root)
        print(f"  Pattern {pattern.pattern}:")
        print(f"    Test file match: {test_match}")
        print(f"    Venv file match: {venv_match}")
    
    # Test overall should_analyze logic
    print("\nOverall analysis decision:")
    test_should_analyze = file_discovery_config.should_analyze_file(test_file)
    venv_should_analyze = file_discovery_config.should_analyze_file(venv_file)
    print(f"Should analyze test file: {test_should_analyze}")
    print(f"Should analyze venv file: {venv_should_analyze}")

if __name__ == "__main__":
    main()