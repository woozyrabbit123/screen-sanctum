# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for ScreenSanctum.

This spec file bundles the entire application including:
- Tesseract OCR binaries (from vendor/)
- Tesseract language data (tessdata)
- Application resources (icons, etc.)
- All Python dependencies

Build with: pyinstaller --noconfirm screensanctum.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the root directory (where this spec file is located)
spec_root = os.path.abspath(SPECPATH)

# Platform-aware Tesseract paths
if sys.platform == "win32":
    tesseract_vendor_dir = ('vendor/tesseract/windows', 'tesseract')
    tessdata_vendor_dir = ('vendor/tesseract/windows/tessdata', 'tessdata')
elif sys.platform == "darwin":
    tesseract_vendor_dir = ('vendor/tesseract/macos', 'tesseract')
    tessdata_vendor_dir = ('vendor/tesseract/macos/tessdata', 'tessdata')
else:  # Assume linux
    tesseract_vendor_dir = ('vendor/tesseract/linux', 'tesseract')
    tessdata_vendor_dir = ('vendor/tesseract/linux/tessdata', 'tessdata')

# Define paths to bundled resources
# NOTE: You must populate vendor/ with Tesseract binaries before building
# vendor/tesseract/{platform}/tesseract(.exe on Windows)
# vendor/tesseract/{platform}/tessdata/eng.traineddata (and other language files)
vendor_tesseract_path = os.path.join(spec_root, tesseract_vendor_dir[0])
vendor_tessdata_path = os.path.join(spec_root, tessdata_vendor_dir[0])
resources_path = os.path.join(spec_root, 'resources')

# Build datas list - these files will be bundled into the executable
datas = []

# Bundle Tesseract binaries (if vendor/ exists)
if os.path.exists(vendor_tesseract_path):
    # Bundle all Tesseract files to 'tesseract/' in the bundle
    datas.append(tesseract_vendor_dir)
    print(f"✓ Found Tesseract binaries in vendor/")
else:
    print(f"⚠ Warning: {tesseract_vendor_dir[0]}/ not found.")
    print("  The built executable will require Tesseract to be installed on the target system.")
    print("  To create a fully standalone build, populate vendor/ with Tesseract binaries.")

# Bundle tessdata separately to ensure it's in the right location
if os.path.exists(vendor_tessdata_path):
    datas.append(tessdata_vendor_dir)
    print(f"✓ Found tessdata in vendor/")
else:
    print(f"⚠ Warning: {tessdata_vendor_dir[0]}/ not found.")

# Bundle application resources (icons, etc.)
if os.path.exists(resources_path):
    datas.append((resources_path, 'resources'))
    print(f"✓ Found resources/")
else:
    print("⚠ Warning: resources/ not found.")

# Collect PySide6 data files (Qt plugins, etc.)
datas += collect_data_files('PySide6')

# Collect any additional data files from dependencies
datas += collect_data_files('platformdirs')

# Hidden imports - modules that PyInstaller might miss
hiddenimports = []
hiddenimports += collect_submodules('PySide6')
hiddenimports += collect_submodules('pytesseract')
hiddenimports += collect_submodules('phonenumbers')
hiddenimports += collect_submodules('cryptography')
hiddenimports += collect_submodules('click')
hiddenimports.append('numpy')
hiddenimports.append('cv2')

# Analysis - find all the modules and files to include
a = Analysis(
    ['src/screensanctum/app.py'],
    pathex=[spec_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'tk',
        'tkinter',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ - Create the archive of Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE - Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScreenSanctum',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False to hide console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(resources_path, 'icons', 'app_icon.ico') if os.path.exists(resources_path) else None,
)

# COLLECT - Gather all files into the distribution directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ScreenSanctum',
)

print("\n" + "=" * 60)
print("PyInstaller Spec File Configuration Summary")
print("=" * 60)
print(f"Entry point: src/screensanctum/app.py")
print(f"Executable name: ScreenSanctum.exe")
print(f"Console window: Hidden (GUI mode)")
print(f"Bundled data files: {len(datas)} items")
print(f"Hidden imports: {len(hiddenimports)} modules")
print("=" * 60)
print("\nTo build:")
print("  pyinstaller --noconfirm screensanctum.spec")
print("\nOutput will be in: dist/ScreenSanctum/")
print("=" * 60 + "\n")
