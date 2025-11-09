# ScreenSanctum v2.0 Gumroad Listing

## Product Title
**ScreenSanctum v2.0 - Offline Screenshot Redaction Tool**

---

## Tagline
Share your screen, not your secrets. Automatic PII detection that runs 100% offline.

---

## Product Description

### What is ScreenSanctum?

ScreenSanctum is a **desktop application** that automatically detects and redacts sensitive information (PII) from screenshots before you share them. Perfect for bug reports, documentation, social media, and email attachments.

**🔒 Offline. No telemetry. Your screenshots never leave your computer.**

---

### Key Features

✨ **Automatic PII Detection** (Pro)
- Detects emails, phone numbers, IP addresses, URLs, hostnames
- Smart OCR engine finds text anywhere in your screenshots
- Pre-selects regions based on customizable templates

🎨 **Multiple Redaction Styles**
- Solid black (default, most secure)
- Blur (softer appearance)
- Pixelate (classic redaction look)

📋 **Clipboard Integration**
- Paste screenshots directly with Ctrl+V
- Copy redacted images back to clipboard
- Fast workflow for quick sharing

⚡ **Batch Processing** (Pro)
- Process entire folders of screenshots at once
- Preserves folder structure
- Creates audit logs for compliance
- Original files never modified

🎯 **Built-in Templates**
- **Social Share Safe**: Aggressive PII removal for social media
- **Bug Report Safe**: Preserves technical details, hides personal info
- **Docs & Email**: Professional redaction for documentation

---

## Basic vs Pro

| Feature | Basic (Free) | Pro |
|---------|--------------|-----|
| Manual redaction | ✅ | ✅ |
| Metadata stripping | ✅ | ✅ |
| Clipboard paste/copy | ✅ | ✅ |
| **Automatic PII detection** | ❌ | ✅ |
| **Batch processing** | ❌ | ✅ |
| **Custom templates** | ❌ | ✅ |
| **Audit logs** | ❌ | ✅ |
| **Priority support** | ❌ | ✅ |

---

## Privacy & Security

- **100% Offline**: No internet connection required. Your screenshots never leave your device.
- **No Telemetry**: We don't collect usage data, crash reports, or analytics.
- **Irreversible Redaction**: Exports are flattened to opaque PNG with all metadata stripped (EXIF, XMP, ICC).
- **Open Source**: Codebase available on GitHub for security audits.

---

## System Requirements

### Windows
- Windows 10 or 11 (64-bit)
- 4GB RAM minimum (8GB recommended for batch processing)
- 500MB disk space

### macOS
- macOS 12 (Monterey) or later
- Intel or Apple Silicon (M1/M2/M3)
- 4GB RAM minimum

### Linux
- Ubuntu 22.04 or equivalent
- 4GB RAM minimum
- Tesseract OCR (bundled or system-installed)

---

## Installation & Usage

### Windows Installation
1. Download `ScreenSanctum_v2.0.0_Windows.zip`
2. Extract to a folder (e.g., `C:\Program Files\ScreenSanctum`)
3. Double-click `ScreenSanctum.exe` to launch

**First-time Windows users**: Windows SmartScreen may show a warning because this is a new application. Click **"More info"** → **"Run anyway"** to proceed. This is expected for unsigned executables.

### macOS Installation
1. Download `ScreenSanctum_v2.0.0_macOS.tar.gz`
2. Extract and drag `ScreenSanctum.app` to `/Applications`
3. **First launch**: Right-click → "Open" to bypass Gatekeeper (not code-signed)

### Entering Your License (Pro Users)
1. Open ScreenSanctum
2. Click **Help** → **Import License**
3. Paste your license key: `SCREENSANCTUM-PRO-XXXX-XXXX-XXXX-XXXX`
4. Click **Activate**

You'll see "✓ Pro license activated" and all Pro features will unlock immediately.

---

## Quick Start Guide

### Basic Workflow
1. **Open** a screenshot (or paste with Ctrl+V)
2. **Auto-Detect** (Pro) or draw boxes manually
3. **Review** detected regions in the sidebar
4. **Export** with your chosen redaction style

### Batch Workflow (Pro)
1. Click **Batch Process** button
2. Select **Input Folder** (your screenshots)
3. Select **Output Folder** (redacted copies will go here)
4. Choose a **Template** (e.g., "Bug Report Safe")
5. Click **Start** and wait for progress bar to complete

**Important**: Originals are never modified. Redacted copies are saved to the output folder only.

---

## Troubleshooting

### "OCR engine not initialized" on Windows
- **Cause**: Tesseract OCR bundle missing or corrupted
- **Fix**: Re-download and extract the ZIP file. Ensure `tesseract/` folder exists next to `ScreenSanctum.exe`

### "Output folder" in batch processing
- **Expected behavior**: Redacted images are saved to a separate output folder
- **Original files**: Never modified. You can safely delete outputs and re-run.

### SmartScreen warning on Windows
- **Expected**: New executables trigger SmartScreen warnings
- **Safe to bypass**: Click "More info" → "Run anyway"

### macOS "App is damaged" error
- **Cause**: Gatekeeper blocking unsigned apps
- **Fix**: Right-click → "Open" on first launch (instead of double-click)

### Batch processing is disabled
- **Cause**: No Pro license detected
- **Fix**: Click "Help" → "Import License" and enter your Pro key

---

## Support & Community

- **GitHub**: https://github.com/woozyrabbit123/screen-sanctum
- **Issues**: Report bugs or request features on GitHub Issues
- **Email**: support@screensanctum.example.com (Pro users: priority response within 24 hours)

---

## Refund Policy

Not satisfied? Request a full refund within **30 days** of purchase. Email support@screensanctum.example.com with your order number.

---

## License Terms

- **Basic**: Free for personal and commercial use
- **Pro**: Lifetime license for 1 user, up to 3 devices
- **No subscription**: One-time payment, own it forever
- **Updates**: Free minor updates (v2.x). Major updates (v3.x) may require upgrade purchase.

---

## What's Included

When you purchase Pro, you get:
- `ScreenSanctum_v2.0.0_Windows.zip` (or macOS/Linux build)
- Pro license key (sent to your email)
- 3 built-in templates (Social Share Safe, Bug Report Safe, Docs & Email)
- Access to all v2.x updates
- Priority email support

---

## Screenshots (Add to Gumroad)

1. **Main Window**: Show screenshot loaded with auto-detected regions highlighted
2. **Sidebar**: Show detected PII list with checkboxes (Email, URL, Phone)
3. **Export Dialog**: Show save dialog with redacted preview
4. **Batch Processing**: Show progress bar and output folder
5. **Template Manager** (Pro): Show custom template editor UI

---

## FAQ

**Q: Does this work without an internet connection?**
A: Yes! ScreenSanctum runs 100% offline. No internet required for any functionality.

**Q: Can I try Pro features before buying?**
A: Basic version is free and includes manual redaction. Pro trial not available, but 30-day refund guarantee applies.

**Q: What PII types are detected?**
A: Emails, phone numbers (international formats), IPv4 addresses, hostnames, URLs (with optional query param flagging).

**Q: Does it detect faces in photos?**
A: Not yet. Face detection is planned for v2.1.

**Q: Can I add custom words to redact?**
A: Yes (Pro). Create custom templates with ignore lists and custom detection rules.

**Q: Is batch processing really safe? Will it delete my originals?**
A: Originals are **never** modified. Redacted copies are saved to a separate output folder. Tested extensively.

**Q: Can I use this commercially?**
A: Yes! Both Basic and Pro licenses allow commercial use (bug reports, documentation, marketing screenshots, etc.).

---

## Version History

**v2.0.0** (Current)
- Desktop GUI with Qt6 interface
- Automatic PII detection (Pro)
- Batch processing with audit logs (Pro)
- Built-in redaction templates (3 included)
- Clipboard integration (Ctrl+V paste, copy to clipboard)
- Metadata stripping (EXIF, XMP, ICC)
- Offline OCR engine (Tesseract)

---

## Developer Note

ScreenSanctum was built because I was tired of manually blurring emails and tokens before sharing bug reports. I wanted a tool that:

1. Runs offline (no privacy concerns)
2. Works fast (OCR + detection in <2 seconds)
3. Doesn't require cloud credits or subscriptions
4. Actually strips metadata (not just "trust us")

Hope you find it useful! 🛡️

— ScreenSanctum Team

---

**[Download ScreenSanctum v2.0 →]**

*Offline. No telemetry. One-time payment.*
