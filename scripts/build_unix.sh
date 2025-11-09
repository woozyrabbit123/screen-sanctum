#!/bin/bash
# ScreenSanctum v2.0 Unix (macOS/Linux) Build Script
# This script builds the Unix distribution package

set -e  # Exit on error

echo "======================================"
echo "ScreenSanctum v2.0 Unix Build"
echo "======================================"
echo ""

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    ARTIFACT_NAME="ScreenSanctum_v2.0.0_macOS"
else
    PLATFORM="Linux"
    ARTIFACT_NAME="ScreenSanctum_v2.0.0_Linux"
fi

echo "Building for: $PLATFORM"
echo ""

# 1. Verify Python 3.11+
echo "[1/6] Verifying Python..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: python3 not found in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo "✓ Found: $PYTHON_VERSION"

MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
    echo "✗ Error: Python 3.11+ required"
    exit 1
fi

# 2. Verify PyInstaller
echo ""
echo "[2/6] Verifying PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo "✗ Error: PyInstaller not found"
    echo "Install with: pip install pyinstaller"
    exit 1
fi

PYINSTALLER_VERSION=$(pyinstaller --version 2>&1)
echo "✓ Found PyInstaller: $PYINSTALLER_VERSION"

# 3. Clean previous builds
echo ""
echo "[3/6] Cleaning previous builds..."
if [ -d "dist/ScreenSanctum" ]; then
    rm -rf "dist/ScreenSanctum"
    echo "✓ Cleaned dist/ScreenSanctum/"
fi
if [ -d "build" ]; then
    rm -rf "build"
    echo "✓ Cleaned build/"
fi

# 4. Run PyInstaller
echo ""
echo "[4/6] Building with PyInstaller..."
echo "This may take several minutes..."
pyinstaller --noconfirm screensanctum.spec
echo "✓ Build complete"

# 5. Create distribution package
echo ""
echo "[5/6] Creating distribution package..."

DIST_DIR="dist/$ARTIFACT_NAME"
if [ -d "$DIST_DIR" ]; then
    rm -rf "$DIST_DIR"
fi
mkdir -p "$DIST_DIR"

# Copy application bundle/directory
cp -R dist/ScreenSanctum/* "$DIST_DIR/"
echo "✓ Copied application"

# Copy README
if [ -f "README.md" ]; then
    cp "README.md" "$DIST_DIR/"
    echo "✓ Copied README.md"
fi

# Copy LICENSE
if [ -f "LICENSE" ]; then
    cp "LICENSE" "$DIST_DIR/LICENSE.txt"
    echo "✓ Copied LICENSE"
elif [ -f "LICENSE.txt" ]; then
    cp "LICENSE.txt" "$DIST_DIR/"
    echo "✓ Copied LICENSE.txt"
fi

# Copy templates
if [ -d "templates" ]; then
    cp -R "templates" "$DIST_DIR/"
    echo "✓ Copied templates/"
fi

# 6. Create tarball archive
echo ""
echo "[6/6] Creating tarball archive..."
TAR_PATH="dist/${ARTIFACT_NAME}.tar.gz"
if [ -f "$TAR_PATH" ]; then
    rm "$TAR_PATH"
fi

cd dist
tar -czf "${ARTIFACT_NAME}.tar.gz" "$ARTIFACT_NAME"
cd ..
echo "✓ Created $TAR_PATH"

# Summary
echo ""
echo "======================================"
echo "Build Complete!"
echo "======================================"
echo ""
echo "Distribution package:"
echo "  📦 $TAR_PATH"
echo ""
echo "Contents:"
echo "  - ScreenSanctum (executable/app)"
echo "  - README.md"
echo "  - LICENSE.txt"
echo "  - templates/ (3 built-in templates)"
echo ""
echo "Next steps:"
echo "  1. Test the build on a fresh $PLATFORM VM"
echo "  2. Run smoke tests (see docs/smoke_test_plan.md)"
if [ "$PLATFORM" == "macOS" ]; then
    echo "  3. (Optional) Code sign for macOS distribution"
    echo "  4. Upload to Gumroad for distribution"
else
    echo "  3. Upload to Gumroad for distribution"
fi
echo ""
