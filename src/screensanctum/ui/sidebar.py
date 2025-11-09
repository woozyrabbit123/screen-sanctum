"""Sidebar widget for detection controls and settings."""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from screensanctum.core.regions import Region


class Sidebar(QWidget):
    """Sidebar widget for controls and settings."""

    # Signal emitted when a region's selection state is toggled
    # Args: (region_index: int, is_checked: bool)
    regionToggled = Signal(int, bool)

    def __init__(self):
        """Initialize the sidebar."""
        super().__init__()
        self._setup_ui()

        # Track regions to prevent signal loops
        self._updating = False

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Title
        title = QLabel("Detected Regions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        # List widget for regions
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.list_widget)

        # Bottom buttons group
        buttons_group = QGroupBox("Export Options")
        buttons_layout = QVBoxLayout()

        # Row 1: Redaction style buttons
        style_layout = QHBoxLayout()

        self.blur_button = QPushButton("Blur Selected")
        self.blur_button.setToolTip("Apply blur redaction to selected regions")
        style_layout.addWidget(self.blur_button)

        self.pixelate_button = QPushButton("Pixelate Selected")
        self.pixelate_button.setToolTip("Apply pixelation to selected regions")
        style_layout.addWidget(self.pixelate_button)

        buttons_layout.addLayout(style_layout)

        # Row 2: Solid and Export buttons
        export_layout = QHBoxLayout()

        self.solid_button = QPushButton("Solid Selected")
        self.solid_button.setToolTip("Apply solid black redaction to selected regions")
        export_layout.addWidget(self.solid_button)

        self.export_button = QPushButton("Export Safe Copy...")
        self.export_button.setToolTip("Export redacted image using default style")
        self.export_button.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #4CAF50; color: white; }"
        )
        export_layout.addWidget(self.export_button)

        buttons_layout.addLayout(export_layout)

        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)

        self.setLayout(layout)

        # Set minimum width
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

    def set_regions(self, regions: List[Region]):
        """Set the regions to display in the list.

        Args:
            regions: List of Region objects.
        """
        # Block signals to prevent loops
        self._updating = True

        # Clear existing items
        self.list_widget.clear()

        # Add items for each region
        for i, region in enumerate(regions):
            # Create display text
            if region.manual:
                display_text = f"Manual Region ({region.w}x{region.h})"
            elif region.pii_type:
                # Truncate text if too long
                text_preview = region.text[:30] + "..." if len(region.text) > 30 else region.text
                display_text = f"{region.pii_type.name}: {text_preview}"
            else:
                display_text = f"Region {i+1}"

            # Create list item
            item = QListWidgetItem(display_text)

            # Set checkable
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Set check state based on region's selected state
            item.setCheckState(Qt.CheckState.Checked if region.selected else Qt.CheckState.Unchecked)

            # Store region index in item data
            item.setData(Qt.ItemDataRole.UserRole, i)

            # Add to list
            self.list_widget.addItem(item)

        # Unblock signals
        self._updating = False

    def _on_item_changed(self, item: QListWidgetItem):
        """Handle item check state change.

        Args:
            item: The item that changed.
        """
        # Ignore if we're updating programmatically
        if self._updating:
            return

        # Get region index
        region_index = item.data(Qt.ItemDataRole.UserRole)

        # Get new check state
        is_checked = item.checkState() == Qt.CheckState.Checked

        # Emit signal
        self.regionToggled.emit(region_index, is_checked)
