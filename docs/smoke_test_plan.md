# ScreenSanctum v2.0 Smoke Test Plan

This document outlines critical smoke tests to run on a **fresh VM** before releasing v2.0 to customers.

## Pre-Test Setup

### Test Environment
- **OS**: Windows 10/11 (or macOS 12+, Ubuntu 22.04+)
- **Status**: Fresh VM or clean user account (no Python, no dependencies)
- **Display**: 1920x1080 minimum resolution

### Test Assets
Create these test images before starting:

1. **test_email_url.png**: Screenshot containing:
   - Email address: `user@example.com`
   - URL with query params: `https://example.com/page?token=abc123&session=xyz789`
   - Phone number: `+1-555-123-4567`

2. **test_2k.png**: 2560x1440 screenshot with mixed PII (for performance test)

3. **test_batch_set/**: Folder with 50+ screenshots (for batch test)

---

## Critical Smoke Tests

### Test 1: Launch & OCR Self-Test ✅
**Goal**: Verify application launches and OCR engine initializes.

**Steps**:
1. Extract `ScreenSanctum_v2.0.0_Windows.zip` to Desktop
2. Double-click `ScreenSanctum.exe`
3. **Windows only**: If SmartScreen appears, click "More info" → "Run anyway"

**Expected**:
- ✅ Application window opens within 5 seconds
- ✅ Status bar shows: "OCR engine initialized" or similar green banner
- ✅ No error dialogs about missing Tesseract

**FAIL if**:
- ❌ "OCR engine not found" error
- ❌ Application crashes on launch
- ❌ Window doesn't appear after 10 seconds

---

### Test 2: Load & Auto-Detect (2K PNG, ≤1.5s) ⚡
**Goal**: Verify fast OCR and detection on high-res images.

**Steps**:
1. Click "Open" and select `test_2k.png` (2560x1440)
2. Start timer
3. Click "Auto-Detect" button
4. Stop timer when detection boxes appear

**Expected**:
- ✅ Bounding boxes appear around email, URL query params within **1.5 seconds**
- ✅ Sidebar shows detected items: "EMAIL: user@..." and "URL: ...?token=..."
- ✅ All detected regions are **pre-selected** (checked)

**FAIL if**:
- ❌ Detection takes >2 seconds on 2K image
- ❌ Email or URL not detected
- ❌ Application freezes during OCR

---

### Test 3: Switch Template (No Re-OCR) 🔄
**Goal**: Verify template switching uses cached OCR results.

**Steps**:
1. With `test_email_url.png` open and OCR results cached:
2. Open template dropdown (top toolbar)
3. Switch from "Default (Solid)" to "Social Share Safe"
4. Observe sidebar and bounding boxes

**Expected**:
- ✅ Template switches **instantly** (no re-OCR spinner)
- ✅ Preselection changes based on new template policy
- ✅ No delay or flickering

**FAIL if**:
- ❌ Re-runs OCR (visible spinner or delay)
- ❌ Bounding boxes disappear then reappear
- ❌ Takes >0.5 seconds to switch

---

### Test 4: Manual Box → Export → Metadata Stripped 🖼️
**Goal**: Verify manual redaction and metadata stripping.

**Steps**:
1. Open `test_email_url.png`
2. Drag a manual bounding box around additional text
3. Right-click the box → "Solid Black"
4. Click "Export Safe Copy" button
5. Save as `output_manual.png`
6. Open `output_manual.png` in a hex editor or metadata viewer (e.g., ExifTool)

**Expected**:
- ✅ Manual box is **solid black** (opaque, not semi-transparent)
- ✅ No EXIF metadata present
- ✅ No XMP metadata present
- ✅ No ICC color profile embedded
- ✅ PNG is **opaque RGB** (no alpha channel)

**FAIL if**:
- ❌ EXIF data still present (e.g., camera model, GPS)
- ❌ Redaction is transparent or reversible
- ❌ Output has alpha channel (RGBA)

---

### Test 5: Paste from Clipboard (Ctrl+V) 📋
**Goal**: Verify clipboard paste workflow.

**Steps**:
1. Take a screenshot using Windows Snipping Tool or macOS Cmd+Shift+4 (do not save to file)
2. Ensure it's in clipboard
3. In ScreenSanctum, press **Ctrl+V** (or Cmd+V on macOS)
4. Auto-detect and export

**Expected**:
- ✅ Screenshot loads from clipboard instantly
- ✅ Auto-detect works normally
- ✅ Export succeeds without requiring a file path

**FAIL if**:
- ❌ Paste does nothing (no image loaded)
- ❌ "Invalid clipboard data" error
- ❌ Application crashes

---

### Test 6: Batch 50 Images → Output Only 📁
**Goal**: Verify batch processing Pro feature (license required).

**Prerequisites**: Import a valid Pro license first (Test 7).

**Steps**:
1. Click "Batch Process" button (toolbar)
2. Set Input: `test_batch_set/` (50+ images)
3. Set Output: `test_batch_set/output/`
4. Select template: "Bug Report Safe"
5. Enable audit log: ✅
6. Click "Start Batch"

**Expected**:
- ✅ Progress bar shows "Processing 1 of 50..."
- ✅ Redacted images appear only in `output/` subfolder
- ✅ **Original images in `test_batch_set/` are untouched**
- ✅ Audit log `.json` receipt created in `output/` folder
- ✅ Batch completes without errors

**FAIL if**:
- ❌ Originals are overwritten or deleted
- ❌ Output images go to wrong directory
- ❌ Batch fails partway through (except for corrupt images)
- ❌ No audit log created

---

### Test 7: Import Pro License → About Shows Masked Details 🔑
**Goal**: Verify license import and display.

**Steps**:
1. Click "Help" → "Import License" (or "About")
2. Paste a valid Pro license key: `SCREENSANCTUM-PRO-XXXX-XXXX-XXXX-XXXX`
3. Click "Activate"
4. Open "Help" → "About"

**Expected**:
- ✅ Success message: "Pro license activated"
- ✅ About dialog shows:
  - Tier: **Pro**
  - Email: `u***r@example.com` (masked)
  - Expiry: `2025-12-31` (or "Lifetime")
- ✅ Batch and template features are unlocked

**FAIL if**:
- ❌ "Invalid license" error for valid key
- ❌ Email shown in plaintext (not masked)
- ❌ Batch button still disabled after activation

---

### Test 8: Non-ASCII Paths Work 🌍
**Goal**: Verify international character support in file paths.

**Steps**:
1. Create a folder: `C:\Users\Test\Screenshots\مجلد_测试_Тест\`
2. Save `test_email_url.png` into this folder
3. Open the image in ScreenSanctum
4. Auto-detect and export to the same folder

**Expected**:
- ✅ Image loads without errors
- ✅ Export succeeds
- ✅ No "Invalid path" or encoding errors

**FAIL if**:
- ❌ "Cannot open file" error
- ❌ Export fails with path encoding error
- ❌ Crash or freeze

---

## Pass Criteria

**Release is GO if**:
- ✅ All 8 tests pass on Windows fresh VM
- ✅ No crashes or data loss
- ✅ OCR performance ≤1.5s for 2K images
- ✅ Metadata stripping works 100%

**DO NOT RELEASE if**:
- ❌ Any test fails on fresh VM
- ❌ OCR not initializing (missing Tesseract bundle)
- ❌ Batch processing overwrites originals
- ❌ Metadata leaks in exported images

---

## Notes

- **Windows SmartScreen**: Expected on first run. Document in Gumroad listing.
- **macOS Gatekeeper**: If not code-signed, users must right-click → "Open" on first launch.
- **Linux**: Tesseract may need system install (`sudo apt install tesseract-ocr`) if not bundled.

**Test on**:
- Windows 10 (fresh VM)
- Windows 11 (fresh VM)
- macOS 12+ (clean user account)
- Ubuntu 22.04 (optional, if offering Linux builds)
