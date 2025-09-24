#!/bin/bash
# Clean up LSP-related temporary files and caches

echo "🧹 Cleaning up LSP-related temporary files..."

# Remove LSP log files
find . -name "*.lsp.log" -type f -delete 2>/dev/null || true
find . -name "lsp-server.log" -type f -delete 2>/dev/null || true
find . -name "language-server.log" -type f -delete 2>/dev/null || true
find . -name "lsp-debug.log" -type f -delete 2>/dev/null || true
find . -name "language-server-debug.log" -type f -delete 2>/dev/null || true

# Remove LSP temporary files
find . -name "*.lsp.tmp" -type f -delete 2>/dev/null || true
find . -name "*.lsp.cache" -type f -delete 2>/dev/null || true
find . -name "*.lsp.pid" -type f -delete 2>/dev/null || true
find . -name "*.lsp.sock" -type f -delete 2>/dev/null || true

# Remove LSP server state directories
rm -rf .drill-sergeant/ 2>/dev/null || true
rm -rf .drill-sergeant-cache/ 2>/dev/null || true
rm -rf .drill-sergeant-lsp/ 2>/dev/null || true
rm -rf .lsp/ 2>/dev/null || true
rm -rf .language-server/ 2>/dev/null || true

# Remove VS Code extension build artifacts
rm -rf vscode-extension/node_modules/ 2>/dev/null || true
rm -rf vscode-extension/out/ 2>/dev/null || true
rm -rf vscode-extension/dist/ 2>/dev/null || true
rm -rf vscode-extension/build/ 2>/dev/null || true
rm -f vscode-extension/*.vsix 2>/dev/null || true

# Remove VS Code test artifacts
rm -rf vscode-extension/.vscode-test/ 2>/dev/null || true
rm -rf vscode-extension/test-results/ 2>/dev/null || true
rm -rf vscode-extension/coverage/ 2>/dev/null || true

echo "✅ LSP cleanup complete!"
echo ""
echo "💡 To rebuild the VS Code extension:"
echo "   cd vscode-extension && npm install && npm run build"
echo ""
echo "💡 To test the LSP server:"
echo "   uv run python -m pytest_drill_sergeant.lsp.main"