"""Main application window for ScreenSanctum."""

from typing import Optional
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QImage

from screensanctum.ui.image_canvas import ImageCanvas
from screensanctum.ui.sidebar import Sidebar
from screensanctum.ui.utils import pil_to_qimage
from screensanctum.core import image_loader, ocr, detection, regions, redaction, config


class SettingsDialog(QDialog):
    """Settings dialog (stub for now)."""

    def __init__(self, app_config: config.AppConfig, parent=None):
        """Initialize settings dialog.

        Args:
            app_config: Current application configuration.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout()

        # Display current config
        layout.addWidget(QLabel("<h2>Current Settings</h2>"))
        layout.addWidget(QLabel(f"Redaction Style: {app_config.redaction_style}"))
        layout.addWidget(QLabel(f"Auto Detect on Open: {app_config.auto_detect_on_open}"))
        layout.addWidget(QLabel(f"OCR Confidence: {app_config.ocr_confidence_threshold}"))
        layout.addWidget(QLabel(f"Show Sidebar: {app_config.show_sidebar}"))
        layout.addWidget(QLabel(f"Theme: {app_config.theme}"))

        layout.addWidget(QLabel("<p><i>Settings editing will be implemented in a future version.</i></p>"))

        self.setLayout(layout)


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
        self.is_pro: bool = True  # Temporary flag for testing (will be licensing-based later)
        self.current_image_path: Optional[str] = None

        # Create menu bar
        self._create_menu_bar()

        # Create central widget with splitter
        self._create_central_widget()

        # Connect signals
        self._connect_signals()

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

            # Run detection
            items = detection.detect_pii(tokens)

            # Build regions
            self.regions = regions.build_regions(items)

            # Update UI
            self.image_canvas.set_regions(self.regions)
            self.sidebar.set_regions(self.regions)

            # Show result
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

    def _on_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.exec()

    def _on_about(self):
        """Handle Help -> About action."""
        QMessageBox.about(
            self,
            "About ScreenSanctum",
            "<h2>ScreenSanctum</h2>"
            "<p><b>Share your screen, not your secrets.</b></p>"
            "<p>Version 0.1.0</p>"
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
