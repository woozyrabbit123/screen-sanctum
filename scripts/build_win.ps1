# ScreenSanctum v2.0 Windows Build Script
# This script builds the Windows distribution package

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "ScreenSanctum v2.0 Windows Build" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verify Python 3.11+
Write-Host "[1/6] Verifying Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green

    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Host "✗ Error: Python 3.11+ required" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "✗ Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

# 2. Verify PyInstaller
Write-Host ""
Write-Host "[2/6] Verifying PyInstaller..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = pyinstaller --version 2>&1
    Write-Host "✓ Found PyInstaller: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: PyInstaller not found" -ForegroundColor Red
    Write-Host "Install with: pip install pyinstaller" -ForegroundColor Yellow
    exit 1
}

# 3. Clean previous builds
Write-Host ""
Write-Host "[3/6] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist/ScreenSanctum") {
    Remove-Item -Recurse -Force "dist/ScreenSanctum"
    Write-Host "✓ Cleaned dist/ScreenSanctum/" -ForegroundColor Green
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "✓ Cleaned build/" -ForegroundColor Green
}

# 4. Run PyInstaller
Write-Host ""
Write-Host "[4/6] Building with PyInstaller..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Gray
try {
    pyinstaller --noconfirm screensanctum.spec
    Write-Host "✓ Build complete" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# 5. Create distribution package
Write-Host ""
Write-Host "[5/6] Creating distribution package..." -ForegroundColor Yellow

$distDir = "dist/ScreenSanctum_v2.0.0_Windows"
if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
}
New-Item -ItemType Directory -Path $distDir | Out-Null

# Copy executable
Copy-Item -Recurse "dist/ScreenSanctum/*" "$distDir/"
Write-Host "✓ Copied executable" -ForegroundColor Green

# Copy README
if (Test-Path "README.md") {
    Copy-Item "README.md" "$distDir/"
    Write-Host "✓ Copied README.md" -ForegroundColor Green
}

# Copy LICENSE
if (Test-Path "LICENSE") {
    Copy-Item "LICENSE" "$distDir/LICENSE.txt"
    Write-Host "✓ Copied LICENSE" -ForegroundColor Green
} elseif (Test-Path "LICENSE.txt") {
    Copy-Item "LICENSE.txt" "$distDir/"
    Write-Host "✓ Copied LICENSE.txt" -ForegroundColor Green
}

# Copy templates
if (Test-Path "templates") {
    Copy-Item -Recurse "templates" "$distDir/"
    Write-Host "✓ Copied templates/" -ForegroundColor Green
}

# 6. Create ZIP archive
Write-Host ""
Write-Host "[6/6] Creating ZIP archive..." -ForegroundColor Yellow
$zipPath = "dist/ScreenSanctum_v2.0.0_Windows.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath
}

Compress-Archive -Path "$distDir/*" -DestinationPath $zipPath
Write-Host "✓ Created $zipPath" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Distribution package:" -ForegroundColor White
Write-Host "  📦 $zipPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Contents:" -ForegroundColor White
Write-Host "  - ScreenSanctum.exe" -ForegroundColor Gray
Write-Host "  - README.md" -ForegroundColor Gray
Write-Host "  - LICENSE.txt" -ForegroundColor Gray
Write-Host "  - templates/ (3 built-in templates)" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the build on a fresh Windows VM" -ForegroundColor White
Write-Host "  2. Run smoke tests (see docs/smoke_test_plan.md)" -ForegroundColor White
Write-Host "  3. Upload to Gumroad for distribution" -ForegroundColor White
Write-Host ""
