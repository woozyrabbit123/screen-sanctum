"""Batch processing dialog for ScreenSanctum."""

from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QCheckBox,
)
from PySide6.QtCore import Qt, QThread

from screensanctum.core.config import AppConfig, RedactionTemplate
from screensanctum.batch.batch_processor import BatchProcessor


class BatchDialog(QDialog):
    """Dialog for batch processing multiple images with redaction templates."""

    def __init__(self, app_config: AppConfig, is_pro: bool, parent=None):
        """Initialize batch dialog.

        Args:
            app_config: Current application configuration.
            is_pro: Whether user has Pro license.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Batch Processing")
        self.setMinimumSize(700, 500)
        self.config = app_config
        self.is_pro = is_pro

        # Batch processing state
        self.input_dir: Optional[str] = None
        self.output_dir: Optional[str] = None
        self.batch_thread: Optional[QThread] = None
        self.batch_processor: Optional[BatchProcessor] = None
        self.processing = False

        layout = QVBoxLayout()

        if not is_pro:
            # Pro feature overlay
            overlay = QLabel(
                "<h2>⭐ Pro Feature</h2>"
                "<p>Batch Processing is a Pro feature.</p>"
                "<p>Upgrade to Pro to process entire folders of images at once.</p>"
            )
            overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            overlay.setStyleSheet("background-color: #f0f0f0; padding: 20px; border: 2px solid #ccc;")
            layout.addWidget(overlay)
        else:
            # Full batch processing UI
            layout.addWidget(QLabel("<h2>Batch Processing</h2>"))
            layout.addWidget(QLabel("Process an entire folder of images with a selected template."))

            # Input directory selection
            input_layout = QHBoxLayout()
            input_layout.addWidget(QLabel("Input Folder:"))
            self.input_label = QLabel("(Not selected)")
            self.input_label.setStyleSheet("color: #666;")
            input_layout.addWidget(self.input_label, 1)
            self.input_button = QPushButton("Browse...")
            self.input_button.clicked.connect(self._on_select_input)
            input_layout.addWidget(self.input_button)
            layout.addLayout(input_layout)

            # Output directory selection
            output_layout = QHBoxLayout()
            output_layout.addWidget(QLabel("Output Folder:"))
            self.output_label = QLabel("(Not selected)")
            self.output_label.setStyleSheet("color: #666;")
            output_layout.addWidget(self.output_label, 1)
            self.output_button = QPushButton("Browse...")
            self.output_button.clicked.connect(self._on_select_output)
            output_layout.addWidget(self.output_button)
            layout.addLayout(output_layout)

            # Template selection
            template_layout = QHBoxLayout()
            template_layout.addWidget(QLabel("Select Template:"))
            self.template_selector = QComboBox()
            self.template_selector.setMinimumWidth(300)

            # Populate with templates
            for template in self.config.templates:
                self.template_selector.addItem(template.name, template.id)

            # Set to active template
            for i, template in enumerate(self.config.templates):
                if template.id == self.config.active_template_id:
                    self.template_selector.setCurrentIndex(i)
                    break

            template_layout.addWidget(self.template_selector, 1)
            layout.addLayout(template_layout)

            # Recursive checkbox
            self.recursive_checkbox = QCheckBox("Process subdirectories recursively")
            self.recursive_checkbox.setChecked(True)
            layout.addWidget(self.recursive_checkbox)

            # Audit log checkbox
            self.audit_log_checkbox = QCheckBox("Create audit log (.json receipt)")
            self.audit_log_checkbox.setChecked(self.config.enable_audit_logs)
            layout.addWidget(self.audit_log_checkbox)

            # Start/Stop button
            button_layout = QHBoxLayout()
            self.start_button = QPushButton("Start Batch")
            self.start_button.clicked.connect(self._on_start_batch)
            self.start_button.setStyleSheet("font-weight: bold; padding: 10px;")
            button_layout.addWidget(self.start_button)

            self.stop_button = QPushButton("Stop")
            self.stop_button.clicked.connect(self._on_stop_batch)
            self.stop_button.setEnabled(False)
            button_layout.addWidget(self.stop_button)
            layout.addLayout(button_layout)

            # Progress bar
            layout.addWidget(QLabel("Progress:"))
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            layout.addWidget(self.progress_bar)

            # Log output
            layout.addWidget(QLabel("Log:"))
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setMaximumHeight(200)
            layout.addWidget(self.log_text)

        # Close button
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_select_input(self):
        """Handle input directory selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Input Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if dir_path:
            self.input_dir = dir_path
            self.input_label.setText(dir_path)
            self.input_label.setStyleSheet("color: black;")

    def _on_select_output(self):
        """Handle output directory selection."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if dir_path:
            self.output_dir = dir_path
            self.output_label.setText(dir_path)
            self.output_label.setStyleSheet("color: black;")

    def _get_selected_template(self) -> Optional[RedactionTemplate]:
        """Get the currently selected template.

        Returns:
            RedactionTemplate object or None if not found.
        """
        template_id = self.template_selector.currentData()
        for template in self.config.templates:
            if template.id == template_id:
                return template
        return None

    def _on_start_batch(self):
        """Start the batch processing."""
        # Validate inputs
        if not self.input_dir:
            self.log_text.append("<b>Error:</b> Please select an input folder.")
            return

        if not self.output_dir:
            self.log_text.append("<b>Error:</b> Please select an output folder.")
            return

        template = self._get_selected_template()
        if not template:
            self.log_text.append("<b>Error:</b> No template selected.")
            return

        # Disable start button and inputs
        self.processing = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.input_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.template_selector.setEnabled(False)
        self.recursive_checkbox.setEnabled(False)
        self.audit_log_checkbox.setEnabled(False)

        # Clear log
        self.log_text.clear()
        self.log_text.append(f"<b>Starting batch processing...</b>")
        self.log_text.append(f"Input: {self.input_dir}")
        self.log_text.append(f"Output: {self.output_dir}")
        self.log_text.append(f"Template: {template.name}")
        self.log_text.append(f"Recursive: {self.recursive_checkbox.isChecked()}")
        self.log_text.append("")

        # Create thread and processor
        self.batch_thread = QThread()
        self.batch_processor = BatchProcessor()
        self.batch_processor.moveToThread(self.batch_thread)

        # Connect signals
        self.batch_processor.progressUpdated.connect(self._on_progress_updated)
        self.batch_processor.fileProcessed.connect(self._on_file_processed)
        self.batch_processor.batchFinished.connect(self._on_batch_finished)

        # Connect thread started signal to run_batch
        recursive = self.recursive_checkbox.isChecked()
        create_audit_log = self.audit_log_checkbox.isChecked()
        self.batch_thread.started.connect(
            lambda: self.batch_processor.run_batch(
                self.input_dir, self.output_dir, template, recursive, create_audit_log
            )
        )

        # Start the thread
        self.batch_thread.start()

    def _on_stop_batch(self):
        """Stop the batch processing."""
        if self.batch_processor:
            self.log_text.append("<b>Stopping batch processing...</b>")
            self.batch_processor.stop()
            self.stop_button.setEnabled(False)

    def _on_progress_updated(self, current: int, total: int):
        """Handle progress update signal.

        Args:
            current: Current file number.
            total: Total number of files.
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")

    def _on_file_processed(self, filename: str, status: str):
        """Handle file processed signal.

        Args:
            filename: Name of the processed file.
            status: Status message (Success or Error: ...).
        """
        if status == "Success":
            self.log_text.append(f"✓ {filename}: {status}")
        else:
            self.log_text.append(f"✗ {filename}: {status}")

        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _on_batch_finished(self, summary: str, audit_log_path: str = ""):
        """Handle batch finished signal.

        Args:
            summary: Summary message.
            audit_log_path: Path to audit log file (if created).
        """
        self.log_text.append("")
        self.log_text.append(f"<b>{summary}</b>")

        if audit_log_path:
            self.log_text.append(f"Audit log saved to: {audit_log_path}")

        # Re-enable controls
        self.processing = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.template_selector.setEnabled(True)
        self.recursive_checkbox.setEnabled(True)
        self.audit_log_checkbox.setEnabled(True)

        # Clean up thread
        if self.batch_thread:
            self.batch_thread.quit()
            self.batch_thread.wait()
            self.batch_thread = None
            self.batch_processor = None

        # Set progress to 100%
        self.progress_bar.setValue(100)

    def closeEvent(self, event):
        """Handle dialog close event.

        Args:
            event: QCloseEvent.
        """
        if self.processing:
            # Stop batch if running
            if self.batch_processor:
                self.batch_processor.stop()
            if self.batch_thread:
                self.batch_thread.quit()
                self.batch_thread.wait()

        event.accept()
