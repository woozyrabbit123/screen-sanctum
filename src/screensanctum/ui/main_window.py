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
    QComboBox,
    QToolBar,
    QTableWidget,
    QTableWidgetItem,
)
from PySide6.QtCore import Qt, QRect, QBuffer, QIODevice
from PySide6.QtGui import QImage, QShortcut, QKeySequence, QGuiApplication

from screensanctum.ui.image_canvas import ImageCanvas
from screensanctum.ui.sidebar import Sidebar
from screensanctum.ui.utils import pil_to_qimage
from screensanctum.ui.batch_dialog import BatchDialog
from screensanctum.core import image_loader, ocr, detection, regions, redaction, config
from screensanctum.licensing import license_check, license_store


class TemplateManagerDialog(QDialog):
    """Template Manager dialog for Pro users to manage redaction templates."""

    def __init__(self, app_config: config.AppConfig, is_pro: bool, parent=None):
        """Initialize template manager dialog.

        Args:
            app_config: Current application configuration.
            is_pro: Whether user has Pro license.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(800, 600)
        self.config = app_config
        self.is_pro = is_pro
        self.selected_template: Optional[config.RedactionTemplate] = None

        layout = QVBoxLayout()

        if not is_pro:
            # Pro feature overlay
            overlay = QLabel("<h2>⭐ Pro Feature</h2>"
                           "<p>Template management is a Pro feature.</p>"
                           "<p>Upgrade to Pro to create, edit, and manage custom redaction templates.</p>")
            overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            overlay.setStyleSheet("background-color: #f0f0f0; padding: 20px; border: 2px solid #ccc;")
            layout.addWidget(overlay)
        else:
            # Full template manager UI
            layout.addWidget(QLabel("<h2>Redaction Templates</h2>"))

            # Main horizontal layout: list on left, editor on right
            main_layout = QHBoxLayout()

            # Left: Template list
            left_layout = QVBoxLayout()
            left_layout.addWidget(QLabel("<b>Templates:</b>"))
            self.template_list = QListWidget()
            self.template_list.currentRowChanged.connect(self._on_template_selected)
            left_layout.addWidget(self.template_list)

            # Buttons for list management
            list_buttons = QHBoxLayout()
            new_btn = QPushButton("New")
            new_btn.clicked.connect(self._on_new_template)
            duplicate_btn = QPushButton("Duplicate")
            duplicate_btn.clicked.connect(self._on_duplicate_template)
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(self._on_delete_template)
            list_buttons.addWidget(new_btn)
            list_buttons.addWidget(duplicate_btn)
            list_buttons.addWidget(delete_btn)
            left_layout.addLayout(list_buttons)

            main_layout.addLayout(left_layout, 1)

            # Right: Template editor
            right_layout = QVBoxLayout()
            right_layout.addWidget(QLabel("<b>Template Editor:</b>"))

            # Template name
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Name:"))
            self.name_edit = QTextEdit()
            self.name_edit.setMaximumHeight(30)
            self.name_edit.setPlaceholderText("Template Name")
            name_layout.addWidget(self.name_edit)
            right_layout.addLayout(name_layout)

            # Ignore lists
            right_layout.addWidget(QLabel("<b>Ignore Lists:</b>"))
            right_layout.addWidget(QLabel("Ignored Emails (one per line):"))
            self.ignored_emails_edit = QTextEdit()
            self.ignored_emails_edit.setPlaceholderText("user@example.com")
            self.ignored_emails_edit.setMaximumHeight(80)
            right_layout.addWidget(self.ignored_emails_edit)

            right_layout.addWidget(QLabel("Ignored Domains (one per line):"))
            self.ignored_domains_edit = QTextEdit()
            self.ignored_domains_edit.setPlaceholderText("example.com")
            self.ignored_domains_edit.setMaximumHeight(80)
            right_layout.addWidget(self.ignored_domains_edit)

            # Default redaction style
            style_layout = QHBoxLayout()
            style_layout.addWidget(QLabel("Default Style:"))
            self.style_combo = QComboBox()
            self.style_combo.addItem("Solid", redaction.RedactionStyle.SOLID)
            self.style_combo.addItem("Blur", redaction.RedactionStyle.BLUR)
            self.style_combo.addItem("Pixelate", redaction.RedactionStyle.PIXELATE)
            style_layout.addWidget(self.style_combo)
            style_layout.addStretch()
            right_layout.addLayout(style_layout)

            # Custom Detection Rules section
            right_layout.addWidget(QLabel("<b>Custom Detection Rules:</b>"))
            self.custom_rules_table = QTableWidget()
            self.custom_rules_table.setColumnCount(2)
            self.custom_rules_table.setHorizontalHeaderLabels(["Rule Name", "Regex Pattern"])
            self.custom_rules_table.horizontalHeader().setStretchLastSection(True)
            self.custom_rules_table.setMaximumHeight(150)
            self.custom_rules_table.cellChanged.connect(self._on_custom_rule_edited)
            right_layout.addWidget(self.custom_rules_table)

            # Custom rules buttons
            custom_rules_buttons = QHBoxLayout()
            self.add_rule_btn = QPushButton("Add Rule")
            self.add_rule_btn.clicked.connect(self._on_add_custom_rule)
            self.remove_rule_btn = QPushButton("Remove Rule")
            self.remove_rule_btn.clicked.connect(self._on_remove_custom_rule)
            custom_rules_buttons.addWidget(self.add_rule_btn)
            custom_rules_buttons.addWidget(self.remove_rule_btn)
            custom_rules_buttons.addStretch()
            right_layout.addLayout(custom_rules_buttons)

            # Pro-gate custom rules if not Pro
            if not self.is_pro:
                self.custom_rules_table.setEnabled(False)
                self.add_rule_btn.setEnabled(False)
                self.remove_rule_btn.setEnabled(False)
                self.custom_rules_table.setToolTip("Pro feature - Upgrade to add custom detection rules")
                self.add_rule_btn.setToolTip("Pro feature - Upgrade to add custom detection rules")
                self.remove_rule_btn.setToolTip("Pro feature - Upgrade to add custom detection rules")

            # Save button for editor
            save_template_btn = QPushButton("Save Template")
            save_template_btn.clicked.connect(self._on_save_template)
            right_layout.addWidget(save_template_btn)

            right_layout.addStretch()
            main_layout.addLayout(right_layout, 2)

            layout.addLayout(main_layout)

            # Populate template list
            self._refresh_template_list()

        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _refresh_template_list(self):
        """Refresh the template list widget."""
        self.template_list.clear()
        for template in self.config.templates:
            self.template_list.addItem(template.name)

    def _on_template_selected(self, row: int):
        """Handle template selection from list."""
        if row < 0 or row >= len(self.config.templates):
            return

        self.selected_template = self.config.templates[row]
        self._load_template_to_editor(self.selected_template)

    def _load_template_to_editor(self, template: config.RedactionTemplate):
        """Load a template's data into the editor."""
        self.name_edit.setPlainText(template.name)
        self.ignored_emails_edit.setPlainText('\n'.join(template.ignore.emails))
        self.ignored_domains_edit.setPlainText('\n'.join(template.ignore.domains))

        # Set style combo box
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == template.style.default:
                self.style_combo.setCurrentIndex(i)
                break

        # Load custom rules into table
        if self.is_pro:
            self._load_custom_rules_to_table(template.custom_rules)

    def _load_custom_rules_to_table(self, custom_rules):
        """Load custom rules into the table widget."""
        # Temporarily disconnect cellChanged to avoid triggering during population
        self.custom_rules_table.cellChanged.disconnect(self._on_custom_rule_edited)

        self.custom_rules_table.setRowCount(0)
        for rule in custom_rules:
            row = self.custom_rules_table.rowCount()
            self.custom_rules_table.insertRow(row)
            self.custom_rules_table.setItem(row, 0, QTableWidgetItem(rule.name))
            self.custom_rules_table.setItem(row, 1, QTableWidgetItem(rule.regex))

        # Reconnect cellChanged signal
        self.custom_rules_table.cellChanged.connect(self._on_custom_rule_edited)

    def _on_save_template(self):
        """Save the current template from editor."""
        if not self.selected_template:
            QMessageBox.warning(self, "No Template Selected", "Please select a template to edit.")
            return

        # Update template from editor
        self.selected_template.name = self.name_edit.toPlainText().strip()
        self.selected_template.ignore.emails = [
            line.strip() for line in self.ignored_emails_edit.toPlainText().split('\n') if line.strip()
        ]
        self.selected_template.ignore.domains = [
            line.strip() for line in self.ignored_domains_edit.toPlainText().split('\n') if line.strip()
        ]
        self.selected_template.style.default = self.style_combo.currentData()

        # Update custom rules from table
        if self.is_pro:
            self.selected_template.custom_rules = []
            for row in range(self.custom_rules_table.rowCount()):
                name_item = self.custom_rules_table.item(row, 0)
                regex_item = self.custom_rules_table.item(row, 1)
                if name_item and regex_item:
                    rule = config.CustomRule(
                        name=name_item.text(),
                        regex=regex_item.text()
                    )
                    self.selected_template.custom_rules.append(rule)

        # Save config
        if config.save_config(self.config):
            self._refresh_template_list()
            QMessageBox.information(self, "Saved", "Template saved successfully.")
        else:
            QMessageBox.warning(self, "Save Error", "Failed to save template.")

    def _on_new_template(self):
        """Create a new template."""
        import uuid
        new_id = f"tpl_custom_{uuid.uuid4().hex[:8]}"
        new_template = config.RedactionTemplate(
            id=new_id,
            name="New Template"
        )
        self.config.templates.append(new_template)
        config.save_config(self.config)
        self._refresh_template_list()
        # Select the new template
        self.template_list.setCurrentRow(len(self.config.templates) - 1)

    def _on_duplicate_template(self):
        """Duplicate the selected template."""
        if not self.selected_template:
            QMessageBox.warning(self, "No Selection", "Please select a template to duplicate.")
            return

        import uuid
        import copy
        new_id = f"tpl_custom_{uuid.uuid4().hex[:8]}"
        new_template = copy.deepcopy(self.selected_template)
        new_template.id = new_id
        new_template.name = f"{self.selected_template.name} (Copy)"
        self.config.templates.append(new_template)
        config.save_config(self.config)
        self._refresh_template_list()

    def _on_delete_template(self):
        """Delete the selected template."""
        if not self.selected_template:
            QMessageBox.warning(self, "No Selection", "Please select a template to delete.")
            return

        # Prevent deleting the last template
        if len(self.config.templates) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "Cannot delete the last template.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{self.selected_template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config.templates.remove(self.selected_template)
            config.save_config(self.config)
            self._refresh_template_list()
            self.selected_template = None

    def _on_add_custom_rule(self):
        """Add a new custom rule to the table."""
        if not self.selected_template:
            QMessageBox.warning(self, "No Template Selected", "Please select a template first.")
            return

        # Add a new row to the table
        row = self.custom_rules_table.rowCount()
        self.custom_rules_table.insertRow(row)
        self.custom_rules_table.setItem(row, 0, QTableWidgetItem("New Rule"))
        self.custom_rules_table.setItem(row, 1, QTableWidgetItem("PATTERN_HERE"))

        # Add to template's custom_rules list immediately
        new_rule = config.CustomRule(name="New Rule", regex="PATTERN_HERE")
        self.selected_template.custom_rules.append(new_rule)

    def _on_remove_custom_rule(self):
        """Remove the selected custom rule from the table."""
        if not self.selected_template:
            return

        current_row = self.custom_rules_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a rule to remove.")
            return

        # Remove from table
        self.custom_rules_table.removeRow(current_row)

        # Remove from template's custom_rules list
        if current_row < len(self.selected_template.custom_rules):
            del self.selected_template.custom_rules[current_row]

    def _on_custom_rule_edited(self, row, column):
        """Handle cell edit in custom rules table."""
        if not self.selected_template:
            return

        # Update the corresponding rule in the template
        if row < len(self.selected_template.custom_rules):
            name_item = self.custom_rules_table.item(row, 0)
            regex_item = self.custom_rules_table.item(row, 1)
            if name_item and regex_item:
                self.selected_template.custom_rules[row].name = name_item.text()
                self.selected_template.custom_rules[row].regex = regex_item.text()


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

        # Create toolbar
        self._create_toolbar()

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

                # Run auto-detection if Pro user
                if self.is_pro:
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

    def get_active_template(self) -> config.RedactionTemplate:
        """Get the currently active redaction template.

        Returns:
            RedactionTemplate object for the active template.
        """
        for template in self.config.templates:
            if template.id == self.config.active_template_id:
                return template
        # Fallback to first template if active not found
        if self.config.templates:
            return self.config.templates[0]
        # Ultimate fallback - create a default template
        return config.RedactionTemplate(id="default", name="Default")

    def get_template_by_id(self, template_id: str) -> Optional[config.RedactionTemplate]:
        """Get a template by its ID.

        Args:
            template_id: ID of the template to retrieve.

        Returns:
            RedactionTemplate object if found, None otherwise.
        """
        for template in self.config.templates:
            if template.id == template_id:
                return template
        return None

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

        # Batch processing action (Pro only)
        batch_action = file_menu.addAction("Run &Batch Process...")
        batch_action.triggered.connect(self._on_batch_process)
        if not self.is_pro:
            batch_action.setEnabled(False)
            batch_action.setToolTip("Pro feature - Upgrade to process folders of images")

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

    def _create_toolbar(self):
        """Create the application toolbar with template selector."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add template selector
        toolbar.addWidget(QLabel("Template: "))
        self.template_selector = QComboBox()
        self.template_selector.setMinimumWidth(200)

        # Populate with templates
        for template in self.config.templates:
            self.template_selector.addItem(template.name, template.id)

        # Set current template
        current_index = 0
        for i, template in enumerate(self.config.templates):
            if template.id == self.config.active_template_id:
                current_index = i
                break
        self.template_selector.setCurrentIndex(current_index)

        # Connect signal
        self.template_selector.currentIndexChanged.connect(self._on_template_changed)

        # Pro gating: disable if not Pro
        if not self.is_pro:
            self.template_selector.setEnabled(False)
            self.template_selector.setToolTip("Pro feature - Upgrade to customize templates")

        toolbar.addWidget(self.template_selector)

    def _on_template_changed(self, index: int):
        """Handle template selection change.

        Args:
            index: Index of selected template in combo box.
        """
        if index < 0:
            return

        # Get selected template ID
        template_id = self.template_selector.itemData(index)
        if not template_id:
            return

        # Update config
        self.config.active_template_id = template_id
        config.save_config(self.config)

        # Re-run detection on current image if loaded
        if self.image and self.is_pro:
            self._run_detection()

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

            # Run auto-detection if Pro user
            if self.is_pro:
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
        """Run OCR and PII detection on the current image using active template."""
        if not self.image:
            return

        try:
            # Get active template
            template = self.get_active_template()

            # Show status message
            self.statusBar().showMessage("Running OCR and detection...", 2000)

            # Run OCR with template's confidence threshold
            tokens = ocr.run_ocr(self.image, conf_threshold=template.ocr_conf)

            # Run detection with template's ignore list
            items = detection.detect_pii(tokens, template.ignore, template.custom_rules)

            # Apply template policy to build regions with proper selection
            self.regions = regions.apply_template_policy(items, template)

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
        """Export using default redaction style from active template."""
        template = self.get_active_template()
        style = template.style.default
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
        """Show template manager dialog."""
        dialog = TemplateManagerDialog(self.config, self.is_pro, self)
        result = dialog.exec()

        # Refresh template selector if templates changed
        if result == QDialog.DialogCode.Accepted:
            # Reload config
            self.config = config.load_config()
            # Refresh template selector
            self.template_selector.clear()
            for template in self.config.templates:
                self.template_selector.addItem(template.name, template.id)
            # Set current template
            for i, template in enumerate(self.config.templates):
                if template.id == self.config.active_template_id:
                    self.template_selector.setCurrentIndex(i)
                    break

    def _on_batch_process(self):
        """Show batch processing dialog."""
        dialog = BatchDialog(self.config, self.is_pro, self)
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
