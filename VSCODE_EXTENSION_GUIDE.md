# 🎖️ VS Code Extension Setup Guide

## What We Just Created

I've created a complete VS Code extension that integrates our LSP server. Here's what you need to know:

## 📁 **Files Created:**

```
vscode-extension/
├── package.json              # Extension manifest
├── tsconfig.json             # TypeScript configuration  
├── src/
│   ├── extension.ts          # Main extension code
│   └── test/                 # Test files
├── install.sh                # Installation script
└── README.md                 # Extension documentation
```

## 🚀 **How to Install & Use:**

### **Option 1: Quick Install (Recommended)**

1. **Install prerequisites**:
   ```bash
   # Make sure you have Node.js installed
   node --version  # Should be 16+
   
   # Make sure pytest-drill-sergeant is installed
   pip install pytest-drill-sergeant[lsp]
   ```

2. **Run the install script**:
   ```bash
   cd vscode-extension
   ./install.sh
   ```

3. **Open VS Code and test**:
   - Open a Python test file (`test_*.py`)
   - Look for red squiggles under violations
   - Use `Ctrl+Shift+P` and search "Drill Sergeant"

### **Option 2: Manual Install**

1. **Install dependencies**:
   ```bash
   cd vscode-extension
   npm install
   ```

2. **Compile TypeScript**:
   ```bash
   npm run compile
   ```

3. **Package extension**:
   ```bash
   npx vsce package
   ```

4. **Install in VS Code**:
   ```bash
   code --install-extension pytest-drill-sergeant-1.0.0-dev.vsix
   ```

## 🎯 **What the Extension Does:**

1. **Starts our LSP server** when you open Python files
2. **Analyzes test files** automatically (test_*.py, *_test.py)
3. **Shows red squiggles** under violations
4. **Provides commands** via Command Palette
5. **Configurable** via VS Code settings

## ⚙️ **Configuration:**

Open VS Code settings (`Ctrl+,`) and search "drill sergeant":

- **Enable/Disable**: `pytest-drill-sergeant.enabled`
- **Persona**: `drill_sergeant` or `snoop_dogg`
- **Severity**: `error`, `warning`, `info`, `hint`
- **Analyze on Save**: Whether to analyze when files are saved

## 🎮 **Commands Available:**

- `Ctrl+Shift+P` → "Drill Sergeant: Analyze Current File"
- `Ctrl+Shift+P` → "Drill Sergeant: Show Analysis Report"

## 🔍 **How It Works:**

1. **VS Code Extension** (TypeScript) starts our **Python LSP Server**
2. **LSP Server** analyzes Python files using our **existing analyzers**
3. **Findings** are converted to **LSP diagnostics**
4. **VS Code** displays diagnostics as **red squiggles**

## 🐛 **Troubleshooting:**

### **Extension Not Working:**

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

### **No Diagnostics Showing:**

- Make sure you're editing a **test file** (`test_*.py` or `*_test.py`)
- Check that the file is in a **test directory** or has **test** in the name
- Try the "Analyze Current File" command manually

### **Performance Issues:**

- Disable "Analyze on Save" in settings
- The extension only analyzes test files, not all Python files

## 🎉 **What You'll See:**

When you open a test file with violations:

```python
# test_example.py
from myapp._internal import secret  # ← Red squiggle here

def test_something():
    obj = SomeClass()
    obj._private_method()           # ← Red squiggle here
    assert obj.__dict__ == data     # ← Red squiggle here
```

**Hover over the squiggles** to see drill sergeant messages like:
> "WHAT IS THIS AMATEUR HOUR?! You're importing PRIVATE modules! DO YOU SNEAK INTO THE SERGEANT'S QUARTERS?!"

## 🚀 **Next Steps:**

1. **Install the extension** using the install script
2. **Test it** on a Python test file with violations
3. **Customize settings** in VS Code preferences
4. **Share feedback** on what works/doesn't work

The extension is **ready to use** and will give you real-time drill sergeant feedback in VS Code! 🎖️