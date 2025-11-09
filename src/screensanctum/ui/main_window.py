"""Main application window for ScreenSanctum."""

from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from screensanctum.ui.image_canvas import ImageCanvas
from screensanctum.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("ScreenSanctum")
        self.setMinimumSize(1000, 700)

        # Create menu bar
        self._create_menu_bar()

        # Create central widget with splitter
        self._create_central_widget()

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
        splitter.setSizes([700, 300])

        # Set as central widget
        self.setCentralWidget(splitter)

    def _on_open_image(self):
        """Handle File -> Open Image action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)",
        )

        if file_path:
            print(f"Selected image: {file_path}")
            # TODO: Load and display the image
            # This will be implemented in a later phase

    def _on_about(self):
        """Handle Help -> About action."""
        QMessageBox.about(
            self,
            "About ScreenSanctum",
            "<h2>ScreenSanctum</h2>"
            "<p><b>Share your screen, not your secrets.</b></p>"
            "<p>Version 0.1.0</p>"
            "<p>An offline-first, cross-platform screenshot redaction tool.</p>"
            "<p>Built with PySide6 and Python.</p>",
        )
