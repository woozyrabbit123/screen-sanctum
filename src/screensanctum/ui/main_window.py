"""Main application window for ScreenSanctum."""

from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QListWidget,
)
from PySide6.QtCore import Qt, QRect, QBuffer, QIODevice
from PySide6.QtGui import QImage, QShortcut, QKeySequence, QGuiApplication

from screensanctum.ui.image_canvas import ImageCanvas
from screensanctum.ui.sidebar import Sidebar
from screensanctum.ui.utils import pil_to_qimage
from screensanctum.core import image_loader, ocr, detection, regions, redaction, config
from screensanctum.licensing import license_check, license_store


class SettingsDialog(QDialog):
    """Settings dialog for configuring trusted domains."""

    def __init__(self, app_config: config.AppConfig, parent=None):
        """Initialize settings dialog.

        Args:
            app_config: Current application configuration.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings - Trusted Domains")
        self.setMinimumSize(500, 400)
        self.config = app_config

        layout = QVBoxLayout()

        # Header
        layout.addWidget(QLabel("<h2>Trusted Domains</h2>"))
        layout.addWidget(QLabel(
            "Emails and domains listed below will be ignored during PII detection.<br>"
            "Enter one domain per line (e.g., example.com or user@example.com)"
        ))

        # List of trusted domains
        self.domains_list = QTextEdit()
        self.domains_list.setPlaceholderText("example.com\nuser@example.com")
        self.domains_list.setPlainText('\n'.join(app_config.trusted_domains))
        layout.addWidget(self.domains_list)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_save(self):
        """Save the trusted domains to config."""
        # Parse domains from text edit
        text = self.domains_list.toPlainText()
        domains = [line.strip() for line in text.split('\n') if line.strip()]

        # Update config
        self.config.trusted_domains = domains

        # Save config
        if config.save_config(self.config):
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Save Error",
                "Failed to save configuration."
            )


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("ScreenSanctum - Share your screen, not your secrets")
        self.setMinimumSize(1200, 800)

        # Application state
        self.image: Optional[Image.Image] = None
        self.qimage: Optional[QImage] = None
        self.regions: list[regions.Region] = []
        self.config: config.AppConfig = config.load_config()
        self.license_data: Optional[license_check.LicenseData] = license_check.get_verified_license()
        self.current_image_path: Optional[str] = None

        # Create menu bar
        self._create_menu_bar()

        # Create central widget with splitter
        self._create_central_widget()

        # Connect signals
        self._connect_signals()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Setup clipboard paste handler
        self._setup_clipboard()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # O - Open Image
        QShortcut(QKeySequence("O"), self).activated.connect(self._on_open_image)

        # E - Export
        QShortcut(QKeySequence("E"), self).activated.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.SOLID)
        )

        # B - Blur
        QShortcut(QKeySequence("B"), self).activated.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.BLUR)
        )

        # X - Solid (X for redact)
        QShortcut(QKeySequence("X"), self).activated.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.SOLID)
        )

        # P - Pixelate
        QShortcut(QKeySequence("P"), self).activated.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.PIXELATE)
        )

    def _setup_clipboard(self):
        """Setup clipboard paste handler."""
        # Ctrl+V / Cmd+V - Paste image from clipboard
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self._on_paste_from_clipboard)

    def _on_paste_from_clipboard(self):
        """Handle pasting image from clipboard."""
        clipboard = QGuiApplication.clipboard()
        qimage = clipboard.image()

        if not qimage.isNull():
            try:
                # Convert QImage to PIL Image
                buffer = QBuffer()
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                qimage.save(buffer, "PNG")
                buffer.close()

                from io import BytesIO
                pil_image = Image.open(BytesIO(buffer.data()))

                # Set the image
                self.image = pil_image
                self.qimage = pil_to_qimage(pil_image)
                self.current_image_path = None  # No file path for clipboard images
                self.regions = []

                # Update UI
                self.image_canvas.set_image(self.qimage)

                # Run auto-detection if pro and enabled
                if self.is_pro and self.config.auto_detect_on_open:
                    self._run_detection()
                else:
                    # No detection - clear regions
                    self.regions = []
                    self.image_canvas.set_regions(self.regions)
                    self.sidebar.set_regions(self.regions)

                self.statusBar().showMessage("Image pasted from clipboard", 2000)

            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Paste Error",
                    f"Failed to paste image from clipboard:\n\n{str(e)}"
                )
        else:
            self.statusBar().showMessage("No image in clipboard", 2000)

    def _update_detection_status(self):
        """Update the status bar with detection counts."""
        total = len(self.regions)
        selected = sum(1 for r in self.regions if r.selected)
        self.statusBar().showMessage(f"Detected: {total} · Selected: {selected}", 0)

    @property
    def is_pro(self) -> bool:
        """Check if user has a valid Pro license.

        Returns:
            True if license is valid and tier is "pro", False otherwise.
        """
        return self.license_data is not None and self.license_data.tier == "pro"

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open Image action
        open_action = file_menu.addAction("&Open Image...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_image)

        file_menu.addSeparator()

        # Copy to clipboard action
        copy_clipboard_action = file_menu.addAction("Copy Safe Copy to &Clipboard")
        copy_clipboard_action.setShortcut("Ctrl+Shift+C")
        copy_clipboard_action.triggered.connect(
            lambda: self._on_copy_to_clipboard(redaction.RedactionStyle.SOLID)
        )

        file_menu.addSeparator()

        # Settings action
        settings_action = file_menu.addAction("&Settings...")
        settings_action.triggered.connect(self._on_settings)

        file_menu.addSeparator()

        # Exit action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Enter License action
        enter_license_action = help_menu.addAction("&Enter License...")
        enter_license_action.triggered.connect(self._on_enter_license)

        help_menu.addSeparator()

        # About action
        about_action = help_menu.addAction("&About ScreenSanctum")
        about_action.triggered.connect(self._on_about)

    def _create_central_widget(self):
        """Create the central widget with image canvas and sidebar."""
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create and add image canvas (left side)
        self.image_canvas = ImageCanvas()
        splitter.addWidget(self.image_canvas)

        # Create and add sidebar (right side)
        self.sidebar = Sidebar()
        splitter.addWidget(self.sidebar)

        # Set initial sizes: 70% for canvas, 30% for sidebar
        splitter.setSizes([840, 360])

        # Set as central widget
        self.setCentralWidget(splitter)

    def _connect_signals(self):
        """Connect all signals from widgets."""
        # Sidebar signals
        self.sidebar.regionToggled.connect(self._on_region_toggled)

        # Sidebar button signals
        self.sidebar.blur_button.clicked.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.BLUR)
        )
        self.sidebar.pixelate_button.clicked.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.PIXELATE)
        )
        self.sidebar.solid_button.clicked.connect(
            lambda: self._on_export_safe_copy(redaction.RedactionStyle.SOLID)
        )
        self.sidebar.export_button.clicked.connect(self._on_export_default)

        # Canvas signals
        self.image_canvas.manualRegionCreated.connect(self._on_manual_region)

    def _on_open_image(self):
        """Handle File -> Open Image action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            str(Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;All Files (*)",
        )

        if not file_path:
            return

        try:
            # Load image using core module
            self.image = image_loader.load_image(file_path)
            self.current_image_path = file_path

            # Convert to QImage for display
            self.qimage = pil_to_qimage(self.image)

            # Display in canvas
            self.image_canvas.set_image(self.qimage)

            # Run auto-detection if pro and enabled
            if self.is_pro and self.config.auto_detect_on_open:
                self._run_detection()
            else:
                # No detection - clear regions
                self.regions = []
                self.image_canvas.set_regions(self.regions)
                self.sidebar.set_regions(self.regions)

            # Update window title with filename
            self.setWindowTitle(f"ScreenSanctum - {Path(file_path).name}")

        except image_loader.ImageLoadError as e:
            QMessageBox.critical(
                self,
                "Error Loading Image",
                f"Failed to load image:\n\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{str(e)}"
            )

    def _run_detection(self):
        """Run OCR and PII detection on the current image."""
        if not self.image:
            return

        try:
            # Show status message
            self.statusBar().showMessage("Running OCR and detection...", 2000)

            # Run OCR
            tokens = ocr.run_ocr(self.image, conf_threshold=self.config.ocr_confidence_threshold)

            # Run detection with trusted domains
            items = detection.detect_pii(tokens, self.config.trusted_domains)

            # Build regions
            self.regions = regions.build_regions(items)

            # Update UI
            self.image_canvas.set_regions(self.regions)
            self.sidebar.set_regions(self.regions)

            # Update status bar with detection counts
            self._update_detection_status()
            self.statusBar().showMessage(f"Detected {len(self.regions)} sensitive regions", 3000)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Detection Error",
                f"Error during detection:\n\n{str(e)}"
            )

    def _on_region_toggled(self, region_index: int, is_checked: bool):
        """Handle region selection toggle from sidebar.

        Args:
            region_index: Index of the region.
            is_checked: New checked state.
        """
        if 0 <= region_index < len(self.regions):
            self.regions[region_index].selected = is_checked
            # Refresh canvas to show visual change
            self.image_canvas.set_regions(self.regions)
            # Update detection status
            self._update_detection_status()

    def _on_manual_region(self, rect: QRect):
        """Handle manual region creation from canvas.

        Args:
            rect: QRect in image coordinates.
        """
        # Create manual region
        new_region = regions.create_manual_region(
            x=rect.x(),
            y=rect.y(),
            w=rect.width(),
            h=rect.height()
        )

        # Add to regions list
        self.regions.append(new_region)

        # Update both canvas and sidebar
        self.image_canvas.set_regions(self.regions)
        self.sidebar.set_regions(self.regions)

        # Show message
        self.statusBar().showMessage("Manual region added", 2000)

    def _on_export_default(self):
        """Export using default redaction style from config."""
        # Map config string to RedactionStyle enum
        style_map = {
            "blur": redaction.RedactionStyle.BLUR,
            "solid": redaction.RedactionStyle.SOLID,
            "pixelate": redaction.RedactionStyle.PIXELATE,
        }

        style = style_map.get(self.config.redaction_style, redaction.RedactionStyle.BLUR)
        self._on_export_safe_copy(style)

    def _on_export_safe_copy(self, style: redaction.RedactionStyle):
        """Export redacted image.

        Args:
            style: RedactionStyle to use for redaction.
        """
        if not self.image:
            QMessageBox.warning(
                self,
                "No Image",
                "Please open an image first."
            )
            return

        # Check if any regions are selected
        selected_regions = [r for r in self.regions if r.selected]
        if not selected_regions:
            reply = QMessageBox.question(
                self,
                "No Regions Selected",
                "No regions are selected for redaction. Export original image?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Get output path
        suggested_name = "redacted.png"
        if self.current_image_path:
            original_path = Path(self.current_image_path)
            suggested_name = f"{original_path.stem}_redacted{original_path.suffix}"

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Redacted Image",
            suggested_name,
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;All Files (*)"
        )

        if not output_path:
            return

        try:
            # Apply redaction
            self.statusBar().showMessage(f"Applying {style.name.lower()} redaction...", 0)

            redacted_image = redaction.apply_redaction(
                self.image,
                self.regions,
                style
            )

            # Save
            redacted_image.save(output_path)

            # Show success
            self.statusBar().showMessage(f"Saved to {output_path}", 5000)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Redacted image saved to:\n\n{output_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export image:\n\n{str(e)}"
            )
            self.statusBar().clearMessage()

    def _on_copy_to_clipboard(self, style: redaction.RedactionStyle):
        """Copy redacted image to clipboard.

        Args:
            style: RedactionStyle to use for redaction.
        """
        if not self.image:
            QMessageBox.warning(
                self,
                "No Image",
                "Please open an image first."
            )
            return

        try:
            # Apply redaction
            self.statusBar().showMessage(f"Applying {style.name.lower()} redaction...", 0)

            redacted_image = redaction.apply_redaction(
                self.image,
                self.regions,
                style
            )

            # Convert PIL Image to QImage
            redacted_qimage = pil_to_qimage(redacted_image)

            # Copy to clipboard
            clipboard = QGuiApplication.clipboard()
            clipboard.setImage(redacted_qimage)

            # Show success
            self.statusBar().showMessage("Redacted image copied to clipboard", 3000)

            QMessageBox.information(
                self,
                "Copied to Clipboard",
                "Redacted image has been copied to clipboard."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Copy Error",
                f"Failed to copy image to clipboard:\n\n{str(e)}"
            )
            self.statusBar().clearMessage()

    def _on_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.exec()

    def _on_enter_license(self):
        """Handle Help -> Enter License action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select License File",
            str(Path.home()),
            "License Files (*.dat *.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            # Read license file
            with open(file_path, 'rb') as f:
                raw_license = f.read()

            # Verify license
            license_data = license_check.verify_license(raw_license)

            if not license_data:
                QMessageBox.critical(
                    self,
                    "Invalid License",
                    "The selected license file is invalid or corrupted.\n\n"
                    "Please check that you have the correct license file."
                )
                return

            # Save license to storage location
            if not license_store.save_license_file(raw_license):
                QMessageBox.warning(
                    self,
                    "Save Error",
                    "License verified successfully, but failed to save.\n\n"
                    "You may need to import the license again next time."
                )
                return

            # Update license data
            self.license_data = license_data

            # Show success
            QMessageBox.information(
                self,
                "License Activated",
                f"<h3>License Successfully Activated!</h3>"
                f"<p><b>Licensed to:</b> {license_data.email}</p>"
                f"<p><b>Tier:</b> {license_data.tier.upper()}</p>"
                f"<p><b>License ID:</b> {license_data.license_id}</p>"
                f"<p>Pro features are now enabled, including automatic PII detection.</p>"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Reading License",
                f"Failed to read license file:\n\n{str(e)}"
            )

    def _on_about(self):
        """Handle Help -> About action."""
        # Build license info section
        if self.is_pro and self.license_data:
            # Mask email (show first char and domain)
            email_parts = self.license_data.email.split('@')
            if len(email_parts) == 2:
                masked_email = f"{email_parts[0][0]}***@{email_parts[1]}"
            else:
                masked_email = "***"

            # Format expiry date
            exp_date = self.license_data.exp.strftime('%Y-%m-%d')

            # Check if expiring soon (< 14 days)
            days_until_expiry = (self.license_data.exp - datetime.utcnow()).days
            expiry_warning = ""
            if days_until_expiry < 14:
                expiry_warning = f"<p style='color: #ff6b35;'><b>⚠ License expires in {days_until_expiry} days!</b></p>"

            license_info = (
                f"<p><b>Tier:</b> {self.license_data.tier.upper()}</p>"
                f"<p><b>Email:</b> {masked_email}</p>"
                f"<p><b>Expires:</b> {exp_date}</p>"
                f"{expiry_warning}"
            )
        else:
            license_info = (
                "<p><b>Running in Basic mode</b></p>"
                "<p>Upgrade to <b>Pro</b> for automatic PII detection.</p>"
                "<p><a href='https://screensanctum.example.com/purchase'>Purchase License</a></p>"
            )

        QMessageBox.about(
            self,
            "About ScreenSanctum",
            "<h2>ScreenSanctum</h2>"
            "<p><b>Share your screen, not your secrets.</b></p>"
            "<p>Version 0.1.0</p>"
            f"{license_info}"
            "<hr>"
            "<p>An offline-first, cross-platform screenshot redaction tool.</p>"
            "<p>Automatically detects and redacts sensitive information including:</p>"
            "<ul>"
            "<li>Email addresses</li>"
            "<li>IP addresses</li>"
            "<li>Phone numbers</li>"
            "<li>URLs and domains</li>"
            "</ul>"
            "<p>Built with PySide6 and Python.</p>"
            "<p><i>Offline-only • Zero telemetry • Privacy-first</i></p>",
        )
