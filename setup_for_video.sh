#!/bin/bash
# MEMORA VIDEO RECORDING - COMPLETE SETUP SCRIPT
# Run this BEFORE recording to ensure clean slate

echo "=== MEMORA VIDEO RECORDING SETUP ==="
echo ""

# Step 1: Clean all old data
echo "[Step 1] Cleaning old data..."
rm -rf memora_data/
rm -rf test_demo/
echo "✓ Old data deleted"
echo ""

# Step 2: Verify directory structure
echo "[Step 2] Verifying project structure..."
if [ -f "pyproject.toml" ]; then
    echo "✓ pyproject.toml found"
else
    echo "✗ ERROR: pyproject.toml not found!"
    exit 1
fi

if [ -d "src/memora" ]; then
    echo "✓ src/memora directory found"
else
    echo "✗ ERROR: src/memora directory not found!"
    exit 1
fi
echo ""

# Step 3: Verify poetry installation
echo "[Step 3] Checking Poetry..."
if command -v poetry &> /dev/null; then
    echo "✓ Poetry is installed"
    poetry --version
else
    echo "✗ ERROR: Poetry not installed!"
    echo "Install with: pip install poetry"
    exit 1
fi
echo ""

# Step 4: Check dependencies
echo "[Step 4] Checking dependencies..."
poetry check > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Dependencies are valid"
else
    echo "✗ ERROR: Dependency issues found"
    echo "Run: poetry install"
    exit 1
fi
echo ""

# Step 5: Verify Ollama
echo "[Step 5] Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
else
    echo "⚠ WARNING: Ollama command not found in PATH"
    echo "Make sure Ollama is running (ollama serve)"
fi
echo ""

# Step 6: Final confirmation
echo "=== SETUP COMPLETE ==="
echo ""
echo "NEXT STEPS FOR RECORDING:"
echo ""
echo "Terminal 1 (Ollama Server):"
echo "  $ ollama serve"
echo ""
echo "Terminal 2 (Memora Proxy):"
echo "  $ cd 'Z:\\Open Source\\FOSS HACK 26\\Memora'"
echo "  $ poetry run memora proxy start"
echo ""
echo "Terminal 3 (Demo Commands - use the script in FOSS_HACK_DEMO.md):"
echo "  $ cd 'Z:\\Open Source\\FOSS HACK 26\\Memora'"
echo "  $ poetry run memora init"
echo "  $ poetry run memora chat --model llama3.2:1b"
echo ""
echo "All data is clean. You're ready to record!"
