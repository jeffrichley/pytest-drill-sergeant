# Python Path Configuration

## Quick Fix for VS Code Extension

The extension needs to find the Python interpreter that has pytest-drill-sergeant installed. Here are two ways to fix this:

### Option 1: Use Full Path (Recommended)

1. **Find your Python path**:
   ```bash
   source .venv/bin/activate
   which python
   ```

2. **Update the extension** to use the full path, or

3. **Create a symlink**:
   ```bash
   sudo ln -s /Users/jeffrichley/workspace/tools/pytest-drill-sergeant/.venv/bin/python /usr/local/bin/drill-sergeant-python
   ```

### Option 2: Install Globally

```bash
pip install pytest-drill-sergeant[lsp]
```

This installs the package globally so any Python command can find it.

### Option 3: VS Code Python Extension

If you have the Python extension installed, VS Code should automatically detect your virtual environment and use the correct Python interpreter.

## Current Issue

The error `spawn python ENOENT` means VS Code can't find the `python` command. This is common on macOS where Python is often installed as `python3`.

## Test Command

To test if your Python can run the LSP server:

```bash
source .venv/bin/activate
python -m pytest_drill_sergeant.lsp.main
```

If this works, then the issue is just VS Code finding the right Python command.