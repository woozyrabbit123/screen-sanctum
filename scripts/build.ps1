# ScreenSanctum Build Script (Windows PowerShell)
#
# This script builds a standalone executable using PyInstaller.
# The resulting executable will be in dist\ScreenSanctum\
#
# Prerequisites:
# - Python 3.11+
# - PyInstaller installed: pip install -e ".[dev]"
# - (Optional) Tesseract binaries in vendor\tesseract\windows\
#
# Usage:
#   .\scripts\build.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ScreenSanctum Build Script (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "Repository root: $RepoRoot"
Write-Host ""

# Check if PyInstaller is installed
try {
    $PyInstallerVersion = & pyinstaller --version 2>&1
    Write-Host "✓ PyInstaller found: $PyInstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: PyInstaller not found!" -ForegroundColor Red
    Write-Host "Please install it with: pip install -e `".[dev]`"" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check for vendor/tesseract (optional but recommended)
if (Test-Path "vendor\tesseract\windows") {
    Write-Host "✓ Found vendor\tesseract\windows\ - will be bundled" -ForegroundColor Green
    Write-Host "  Tesseract files:"
    Get-ChildItem -Path "vendor\tesseract\windows" -Recurse -File | Select-Object -First 5 | ForEach-Object {
        Write-Host "    $($_.FullName.Replace($RepoRoot, '.'))"
    }
    $FileCount = (Get-ChildItem -Path "vendor\tesseract\windows" -Recurse -File).Count
    if ($FileCount -gt 5) {
        Write-Host "    ... and $($FileCount - 5) more files"
    }
} else {
    Write-Host "⚠ Warning: vendor\tesseract\windows\ not found" -ForegroundColor Yellow
    Write-Host "  The built executable will require Tesseract to be installed on the target system."
    Write-Host "  To create a fully standalone build:"
    Write-Host "    1. Download Tesseract binaries for Windows"
    Write-Host "    2. Place them in vendor\tesseract\windows\"
    Write-Host "    3. Re-run this build script"
}
Write-Host ""

# Check for resources/icons
if (Test-Path "resources\icons") {
    Write-Host "✓ Found resources\icons\" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: resources\icons\ not found" -ForegroundColor Yellow
}
Write-Host ""

# Clean previous builds
if (Test-Path "build") {
    Write-Host "Cleaning build\ directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "build"
}

if (Test-Path "dist") {
    Write-Host "Cleaning dist\ directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}
Write-Host ""

# Run PyInstaller
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

& pyinstaller --noconfirm screensanctum.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "dist\ScreenSanctum") {
    Write-Host "✓ Executable built successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Output location: dist\ScreenSanctum\"
    Write-Host "Executable: dist\ScreenSanctum\ScreenSanctum.exe"
    Write-Host ""

    # Show size
    $DistSize = (Get-ChildItem -Path "dist\ScreenSanctum" -Recurse | Measure-Object -Property Length -Sum).Sum
    $DistSizeMB = [math]::Round($DistSize / 1MB, 2)
    Write-Host "Total size: $DistSizeMB MB"
    Write-Host ""

    Write-Host "To run the executable:"
    Write-Host "  .\dist\ScreenSanctum\ScreenSanctum.exe"
    Write-Host ""

    Write-Host "To create a distributable archive:"
    Write-Host "  Compress-Archive -Path dist\ScreenSanctum -DestinationPath ScreenSanctum-Windows-x64.zip"
    Write-Host ""

    # Optional: Create installer with Inno Setup or NSIS
    Write-Host "To create a Windows installer:"
    Write-Host "  1. Install Inno Setup: https://jrsoftware.org/isdl.php"
    Write-Host "  2. Create an .iss script file"
    Write-Host "  3. Run: iscc your-installer-script.iss"
    Write-Host ""
} else {
    Write-Host "✗ Build failed - output directory not found" -ForegroundColor Red
    exit 1
}

Write-Host "==========================================" -ForegroundColor Cyan
