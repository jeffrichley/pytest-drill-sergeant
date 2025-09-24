#!/bin/bash

# Install script for pytest-drill-sergeant VS Code extension

set -e

echo "🎖️ Installing Pytest Drill Sergeant VS Code Extension"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the vscode-extension directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed. Please install npm first."
    exit 1
fi

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "❌ Error: VS Code command line tool not found."
    echo "   Please install VS Code and add it to your PATH."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Compile TypeScript
echo "🔨 Compiling TypeScript..."
npm run compile

# Package the extension
echo "📦 Packaging extension..."
npx vsce package

# Find the generated .vsix file
VSIX_FILE=$(find . -name "*.vsix" -type f | head -1)

if [ -z "$VSIX_FILE" ]; then
    echo "❌ Error: Failed to create .vsix package"
    exit 1
fi

echo "✅ Extension packaged: $VSIX_FILE"

# Install the extension
echo "🚀 Installing extension in VS Code..."
code --install-extension "$VSIX_FILE"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To use the extension:"
echo "1. Open VS Code"
echo "2. Open a Python test file (test_*.py)"
echo "3. Look for red squiggles under violations"
echo "4. Use Ctrl+Shift+P and search for 'Drill Sergeant' commands"
echo ""
echo "Make sure pytest-drill-sergeant is installed:"
echo "  pip install pytest-drill-sergeant[lsp]"
echo ""
