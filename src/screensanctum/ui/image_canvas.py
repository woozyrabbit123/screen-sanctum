"""Image canvas widget for displaying and editing images."""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class ImageCanvas(QWidget):
    """Canvas widget for displaying and interacting with images."""

    def __init__(self):
        """Initialize the image canvas."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Placeholder label
        label = QLabel("Image Canvas Area")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "QLabel { "
            "background-color: #f0f0f0; "
            "border: 2px dashed #cccccc; "
            "padding: 20px; "
            "font-size: 14px; "
            "color: #666666; "
            "}"
        )

        layout.addWidget(label)
        self.setLayout(layout)
