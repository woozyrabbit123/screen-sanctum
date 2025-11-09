"""Sidebar widget for detection controls and settings."""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class Sidebar(QWidget):
    """Sidebar widget for controls and settings."""

    def __init__(self):
        """Initialize the sidebar."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Placeholder label
        label = QLabel("Sidebar Controls")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "QLabel { "
            "background-color: #fafafa; "
            "border: 1px solid #dddddd; "
            "padding: 20px; "
            "font-size: 14px; "
            "color: #666666; "
            "}"
        )

        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)
