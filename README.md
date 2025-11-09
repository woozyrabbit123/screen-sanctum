# ScreenSanctum

**Share your screen, not your secrets.**

![ScreenSanctum Demo](https://placeholder.com/screensanctum-demo.gif)
*[Demo GIF placeholder - Add actual demo GIF here]*

---

## What is ScreenSanctum?

ScreenSanctum is an **offline-first screenshot redaction tool** that protects your privacy before you share images. Whether you're sharing screenshots for bug reports, tutorials, or presentations, ScreenSanctum ensures sensitive information never leaves your control.

**Everything runs locally on your machine.** No cloud processing, no servers, no internet required. Your screenshots never leave your computer.

---

## 🔒 Core Privacy Stance

- **🚫 Zero Telemetry**: We don't collect, track, or transmit any data. Ever.
- **💻 Offline-Only**: All processing happens locally. No network requests, no cloud dependencies.
- **🔐 Nothing Leaves Your Machine**: Your images, your data, your control.
- **🛡️ Metadata Stripping**: All exported images have EXIF/XMP/ICC metadata removed.
- **🎯 Permanent Redaction**: Redacted areas cannot be reversed or recovered.

---

## ✨ Features

### Basic (Free)

The free tier gives you powerful manual redaction capabilities:

- ✅ **Manual Redaction**: Draw boxes around sensitive areas
- ✅ **Three Redaction Styles**: Solid (default), Blur, or Pixelate
- ✅ **Metadata Stripping**: All EXIF/GPS/camera data removed from exports
- ✅ **Permanent Redaction**: Flattened to RGB, no alpha channel data leakage
- ✅ **Clipboard Support**: Paste images with `Ctrl+V`, copy redacted images with `Ctrl+Shift+C`
- ✅ **Keyboard Shortcuts**: Fast workflow with `O` (open), `E` (export), `B` (blur), `X` (solid), `P` (pixelate)
- ✅ **Cross-Platform**: Windows, macOS, and Linux

### Pro (Paid License)

Upgrade to Pro for automatic detection and advanced features:

- 🚀 **All Basic Features**, PLUS:
- 🤖 **Automatic PII Detection**: Automatically finds and highlights:
  - 📧 Email addresses
  - 🌐 IP addresses
  - 🔗 URLs and domains
  - 📱 Phone numbers (international format support)
- ⚙️ **Trusted Patterns**: Whitelist your own email/domain to skip detection
- 💻 **CLI Access**: Automate redaction with `screensanctum-cli` for batch processing
- 📊 **Detection Status**: Real-time counter showing detected/selected regions
- 🔄 **Key Rotation**: Enterprise-grade license system with time-based validation

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- Tesseract OCR (required for automatic detection in Pro mode)

**Install Tesseract:**

```bash
# macOS (Homebrew)
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows (Chocolatey)
choco install tesseract

# Or download from: https://github.com/tesseract-ocr/tesseract
```

### Install ScreenSanctum

```bash
# Clone the repository
git clone https://github.com/woozyrabbit123/screen-sanctum.git
cd screen-sanctum

# Install with pip
pip install -e .

# Run the GUI
screensanctum
```

---

## 📖 Usage

### GUI Mode

1. **Open an Image**
   - Click `File → Open Image...` or press `Ctrl+O`
   - Or paste from clipboard with `Ctrl+V`

2. **Review Detections** (Pro only)
   - If you have a Pro license and auto-detect is enabled, sensitive information is automatically highlighted
   - Toggle regions on/off in the sidebar
   - Draw additional manual regions by clicking and dragging

3. **Export Safe Copy**
   - Choose your redaction style: Blur, Solid, or Pixelate
   - Click the corresponding button or use keyboard shortcuts (`B`, `X`, `P`)
   - Or copy directly to clipboard with `Ctrl+Shift+C`

### CLI Mode (Pro only)

The CLI is perfect for automation and batch processing:

```bash
# Basic usage (strips metadata, no detection)
screensanctum-cli redact --input screenshot.png --output safe.png

# Pro: Automatic PII detection
screensanctum-cli redact --input screenshot.png --output safe.png --auto

# With custom style and trusted domains
screensanctum-cli redact \
  --input screenshot.png \
  --output safe.png \
  --auto \
  --style blur \
  --trusted-domains example.com \
  --trusted-domains user@company.com

# Get help
screensanctum-cli redact --help
```

**CLI Options:**

- `--input`: Path to input image file (required)
- `--output`: Path to save redacted output (required)
- `--style`: Redaction style: `solid`, `blur`, or `pixelate` (default: `solid`)
- `--auto`: Enable automatic PII detection (requires Pro license)
- `--trusted-domains`: Domains/emails to skip during detection (can be used multiple times)

---

## 🔑 Licensing

### How to Activate Pro

1. **Purchase a License**
   - Visit: [https://screensanctum.example.com/purchase](https://screensanctum.example.com/purchase)
   - You'll receive a `license.dat` file via email

2. **Install Your License**
   - **Option 1 (GUI)**: Click `Help → Enter License...` and select your `license.dat` file
   - **Option 2 (Manual)**: Place `license.dat` in the ScreenSanctum data directory:
     - **Linux**: `~/.local/share/ScreenSanctum/license.dat`
     - **macOS**: `~/Library/Application Support/ScreenSanctum/license.dat`
     - **Windows**: `%LOCALAPPDATA%\ScreenSanctum\license.dat`

3. **Verify Activation**
   - Click `Help → About ScreenSanctum`
   - You should see your license details and expiry date
   - Pro features (auto-detection, CLI) are now enabled

### License Details

- ✅ **One-time purchase** (no subscription)
- ✅ **Works offline** (no license server checks)
- ✅ **Time-based validation** (expiry date is verified locally)
- ✅ **Secure verification** (ECDSA cryptographic signatures)
- ✅ **Grace period** (5-minute clock skew tolerance)

---

## 🎨 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open image |
| `Ctrl+V` | Paste image from clipboard |
| `O` | Open image (alternative) |
| `E` | Export with current style |
| `B` | Export with Blur style |
| `X` | Export with Solid (redact) style |
| `P` | Export with Pixelate style |
| `Ctrl+Shift+C` | Copy redacted image to clipboard |
| `Ctrl+Q` | Quit application |

---

## 🖥️ Platform Support

ScreenSanctum is built with cross-platform compatibility in mind:

| Platform | Status | Notes |
|----------|--------|-------|
| **Linux** | ✅ Fully Supported | Tested on Ubuntu 20.04+ |
| **macOS** | ✅ Fully Supported | macOS 11+ (Intel & Apple Silicon) |
| **Windows** | ✅ Fully Supported | Windows 10+ |

---

## 🛠️ Technical Details

### Security Features

- **Canonical JSON**: License signatures use sorted keys and no whitespace to prevent bypass attacks
- **Key Rotation**: Support for multiple public keys via `kid` (key ID) field
- **Time-Based Validation**: Licenses include `nbf` (not before) and `exp` (expiry) timestamps
- **Metadata Stripping**: All EXIF, XMP, and ICC profiles are removed from exported images
- **RGB Flattening**: Images are converted to opaque RGB to prevent alpha channel data leakage

### Detection Capabilities

The Pro tier's automatic detection uses:

- **OCR**: Tesseract for text extraction with confidence thresholds
- **Regex Patterns**: For emails, IPs, URLs, and domains
- **Phone Number Library**: International phone number validation via `phonenumbers`
- **Bounding Box Mapping**: Precise character-to-pixel coordinate mapping

### HiDPI/Retina Support

- Separate coordinate spaces for source images and display
- Proper scaling prevents pixel data loss on high-resolution displays
- All mouse events emit source coordinates, not scaled coordinates

---

## 🤝 Contributing

ScreenSanctum is currently in active development. Contributions, bug reports, and feature requests are welcome!

**Areas for Contribution:**

- Additional PII detection patterns
- UI/UX improvements
- Documentation and tutorials
- Platform-specific packaging (e.g., .deb, .dmg, .exe installers)

Please open an issue or pull request on GitHub.

---

## 📄 License

ScreenSanctum is released under the **MIT License**.

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:

- **PySide6** - Qt6 GUI framework
- **Pillow** - Image processing
- **Tesseract OCR** - Text extraction
- **Click** - CLI framework
- **Cryptography** - ECDSA license verification

---

## 📞 Support

- **Issues & Bugs**: [GitHub Issues](https://github.com/woozyrabbit123/screen-sanctum/issues)
- **Documentation**: [GitHub Wiki](https://github.com/woozyrabbit123/screen-sanctum/wiki)
- **Purchase Pro License**: [https://screensanctum.example.com/purchase](https://screensanctum.example.com/purchase)

---

<p align="center">
  <strong>Share your screen, not your secrets.</strong><br>
  Made with ❤️ for privacy-conscious users everywhere.
</p>
