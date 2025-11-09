#!/bin/bash
#
# ScreenSanctum Build Script (Linux/macOS)
#
# This script builds a standalone executable using PyInstaller.
# The resulting executable will be in dist/ScreenSanctum/
#
# Prerequisites:
# - Python 3.11+
# - PyInstaller installed: pip install -e ".[dev]"
# - (Optional) Tesseract binaries in vendor/tesseract/
#
# Usage:
#   ./scripts/build.sh

set -e  # Exit on error

echo "=========================================="
echo "ScreenSanctum Build Script"
echo "=========================================="
echo ""

# Get the script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "Repository root: $REPO_ROOT"
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "ERROR: PyInstaller not found!"
    echo "Please install it with: pip install -e \".[dev]\""
    exit 1
fi

echo "✓ PyInstaller found: $(pyinstaller --version)"
echo ""

# Check for vendor/tesseract (optional but recommended)
if [ -d "vendor/tesseract" ]; then
    echo "✓ Found vendor/tesseract/ - will be bundled"
    echo "  Tesseract files:"
    find vendor/tesseract -type f | head -n 5
    if [ $(find vendor/tesseract -type f | wc -l) -gt 5 ]; then
        echo "  ... and $(( $(find vendor/tesseract -type f | wc -l) - 5 )) more files"
    fi
else
    echo "⚠ Warning: vendor/tesseract/ not found"
    echo "  The built executable will require Tesseract to be installed on the target system."
    echo "  To create a fully standalone build:"
    echo "    1. Download Tesseract binaries for your platform"
    echo "    2. Place them in vendor/tesseract/[platform]/"
    echo "    3. Re-run this build script"
fi
echo ""

# Check for resources/icons
if [ -d "resources/icons" ]; then
    echo "✓ Found resources/icons/"
else
    echo "⚠ Warning: resources/icons/ not found"
fi
echo ""

# Clean previous builds
if [ -d "build" ]; then
    echo "Cleaning build/ directory..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Cleaning dist/ directory..."
    rm -rf dist
fi
echo ""

# Run PyInstaller
echo "=========================================="
echo "Running PyInstaller..."
echo "=========================================="
echo ""

pyinstaller --noconfirm screensanctum.spec

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""

if [ -d "dist/ScreenSanctum" ]; then
    echo "✓ Executable built successfully!"
    echo ""
    echo "Output location: dist/ScreenSanctum/"
    echo "Executable: dist/ScreenSanctum/ScreenSanctum"
    echo ""

    # Show size
    DIST_SIZE=$(du -sh dist/ScreenSanctum | cut -f1)
    echo "Total size: $DIST_SIZE"
    echo ""

    echo "To run the executable:"
    echo "  ./dist/ScreenSanctum/ScreenSanctum"
    echo ""

    echo "To create a distributable archive:"
    echo "  cd dist"
    echo "  tar -czf ScreenSanctum-$(uname -s)-$(uname -m).tar.gz ScreenSanctum/"
    echo ""
else
    echo "✗ Build failed - output directory not found"
    exit 1
fi

echo "=========================================="
