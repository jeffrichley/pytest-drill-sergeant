# Example Files

This directory contains example test files that demonstrate various violations that `pytest-drill-sergeant` can detect. These files are intentionally written to trigger specific analyzer violations and are used for:

1. **Testing the analyzers** - Ensuring they correctly detect violations
2. **Documentation** - Showing users what violations look like
3. **Examples** - Demonstrating how to fix common test quality issues

## Files

- `test_aaa_sample.py` - Examples of AAA (Arrange-Act-Assert) comment structure violations
- `test_dogfood.py` - Simple examples of private access and mock over-specification
- `test_mock_overspec_sample.py` - Examples of mock over-specification violations
- `test_structural_equality_sample.py` - Examples of structural equality violations
- `sample_code/` - Additional test examples with various violation types

## Usage

These files can be analyzed with:

```bash
uv run python -m pytest_drill_sergeant lint examples/
```

**Note**: These are example files with intentional violations. They should not be used as templates for real test code!
