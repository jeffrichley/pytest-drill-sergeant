# Pytest Drill Sergeant VS Code Extension

🎖️ **AI test quality enforcement tool with military-themed feedback**

This VS Code extension integrates the pytest-drill-sergeant LSP server to provide real-time diagnostics for test quality issues.

## Features

- 🔍 **Real-time Analysis** - Analyzes Python test files as you type
- 🎖️ **Military-themed Feedback** - Drill sergeant persona with humor
- ⚠️ **Error Squiggles** - Shows violations as red squiggles in your IDE
- 📊 **Multiple Analyzers** - Detects private access, mock over-specification, structural equality, and AAA violations
- 🎯 **Test File Focus** - Only analyzes test files (test_*.py, *_test.py, files in test/ directories)

## Installation

### Prerequisites

1. **Python 3.11+** installed on your system
2. **pytest-drill-sergeant** package installed:
   ```bash
   pip install pytest-drill-sergeant[lsp]
   ```

### Install Extension

1. **From VSIX file** (when available):
   ```bash
   code --install-extension pytest-drill-sergeant-1.0.0-dev.vsix
   ```

2. **From source** (development):
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   # Then package and install
   ```

## Configuration

Open VS Code settings and search for "drill sergeant":

- **Enable/Disable**: `pytest-drill-sergeant.enabled`
- **Persona**: Choose between `drill_sergeant` or `snoop_dogg`
- **Severity Level**: Minimum severity to show (`error`, `warning`, `info`, `hint`)
- **Analyze on Save**: Whether to analyze files when saved

## Usage

1. **Open a Python test file** (test_*.py or *_test.py)
2. **See violations** as red squiggles under problematic code
3. **Hover over squiggles** to see drill sergeant messages
4. **Use Command Palette** (`Ctrl+Shift+P`):
   - `Drill Sergeant: Analyze Current File`
   - `Drill Sergeant: Show Analysis Report`

## Example Violations

```python
# Private import violation
from myapp._internal import secret_function  # ← Red squiggle

def test_something():
    obj = SomeClass()
    obj._private_method()  # ← Red squiggle

    # Structural equality violation
    assert obj.__dict__ == expected_dict  # ← Red squiggle
```

## Commands

- `pytest-drill-sergeant.analyzeFile` - Analyze the current file
- `pytest-drill-sergeant.showReport` - Show the analysis output

## Troubleshooting

### Extension Not Working

1. **Check Python installation**:
   ```bash
   python --version  # Should be 3.11+
   ```

2. **Check package installation**:
   ```bash
   python -c "import pytest_drill_sergeant; print('OK')"
   ```

3. **Check VS Code output**:
   - Open Output panel (`Ctrl+Shift+U`)
   - Select "Drill Sergeant" from dropdown
   - Look for error messages

### Common Issues

- **"Command not found"**: Make sure pytest-drill-sergeant is installed with LSP support
- **No diagnostics**: Check that you're editing a test file (test_*.py)
- **Performance issues**: Disable "Analyze on Save" in settings

## Development

To contribute or modify the extension:

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   cd vscode-extension
   npm install
   ```

3. **Compile TypeScript**:
   ```bash
   npm run compile
   ```

4. **Run in development**:
   - Press `F5` in VS Code to open Extension Development Host
   - Test the extension in the new window

## License

MIT License - see main project LICENSE file.
