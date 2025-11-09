# Vendor Directory

This directory contains third-party binaries that are bundled into the standalone executable.

## Tesseract OCR

To create a fully standalone, offline executable, you need to place Tesseract binaries and language data in this directory.

### Directory Structure

```
vendor/
├── tesseract/
│   ├── windows/
│   │   ├── tesseract.exe
│   │   ├── *.dll (required DLLs)
│   │   └── tessdata/
│   │       ├── eng.traineddata
│   │       └── [other language files]
│   ├── linux/
│   │   ├── tesseract
│   │   └── tessdata/
│   │       └── eng.traineddata
│   └── macos/
│       ├── tesseract
│       └── tessdata/
│           └── eng.traineddata
```

### Where to Get Tesseract Binaries

#### Windows

1. **Official Installer Method**:
   - Download Tesseract installer: https://github.com/UB-Mannheim/tesseract/wiki
   - Install Tesseract to a temporary location
   - Copy the following from the installation directory to `vendor/tesseract/windows/`:
     - `tesseract.exe`
     - All `.dll` files (leptonica, libjpeg, libpng, etc.)
     - The entire `tessdata/` folder

2. **Manual Binary Method**:
   - Download pre-built binaries from: https://digi.bib.uni-mannheim.de/tesseract/
   - Extract and copy to `vendor/tesseract/windows/`

#### Linux

1. **From System Installation**:
   ```bash
   # Install Tesseract
   sudo apt-get install tesseract-ocr

   # Copy binary
   cp $(which tesseract) vendor/tesseract/linux/

   # Copy tessdata
   cp -r /usr/share/tesseract-ocr/*/tessdata vendor/tesseract/linux/
   ```

2. **Build from Source**:
   - Follow instructions at: https://github.com/tesseract-ocr/tesseract
   - Copy built binary and tessdata to `vendor/tesseract/linux/`

#### macOS

1. **Using Homebrew**:
   ```bash
   # Install Tesseract
   brew install tesseract

   # Copy binary
   cp $(which tesseract) vendor/tesseract/macos/

   # Copy tessdata
   cp -r $(brew --prefix)/share/tessdata vendor/tesseract/macos/
   ```

### Minimal vs Full Installation

**Minimal Installation** (recommended for smaller executable):
- Only include `eng.traineddata` (English language support)
- Executable size: ~50-100 MB

**Full Installation**:
- Include all language files from tessdata
- Executable size: ~500+ MB

### Language Files

Language data files are available at:
- Official: https://github.com/tesseract-ocr/tessdata
- Fast (smaller, less accurate): https://github.com/tesseract-ocr/tessdata_fast
- Best (larger, more accurate): https://github.com/tesseract-ocr/tessdata_best

Common language files:
- `eng.traineddata` - English
- `fra.traineddata` - French
- `deu.traineddata` - German
- `spa.traineddata` - Spanish
- `chi_sim.traineddata` - Chinese (Simplified)
- `jpn.traineddata` - Japanese

### Build Without Bundled Tesseract

If you don't populate the `vendor/` directory, the build will still succeed, but:
- The executable will require Tesseract to be installed on the target system
- Users will see an error if Tesseract is not found
- Auto-detection (Pro feature) will be disabled

This is acceptable for:
- Development builds
- Distribution to users who already have Tesseract installed
- Environments where you control the Tesseract installation

### Verification

After populating `vendor/tesseract/`, verify the structure:

```bash
# Check structure
ls -R vendor/tesseract/

# Windows example output:
# vendor/tesseract/windows/tesseract.exe
# vendor/tesseract/windows/leptonica-*.dll
# vendor/tesseract/windows/tessdata/eng.traineddata
```

The PyInstaller spec file (`screensanctum.spec`) will automatically detect and bundle these files when you run the build script.

### .gitignore

The `vendor/` directory is typically added to `.gitignore` because:
- Binary files are large and not suitable for git
- Users download Tesseract based on their platform
- Each developer may have different versions

To distribute Tesseract with your builds:
- Create platform-specific archives (zip, tar.gz)
- Upload to GitHub Releases or other hosting
- Document download instructions for users
