"""Image canvas widget for displaying and editing images."""

from typing import Optional, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QImage, QColor, QPen
from screensanctum.core.regions import Region


class ImageCanvas(QWidget):
    """Canvas widget for displaying and interacting with images."""

    # Signal emitted when user creates a manual region
    manualRegionCreated = Signal(QRect)

    def __init__(self):
        """Initialize the image canvas."""
        super().__init__()

        # Image and regions state
        self.qimage: Optional[QImage] = None
        self.regions: List[Region] = []

        # Manual region drawing state
        self.drawing = False
        self.draw_start: Optional[QPoint] = None
        self.draw_current: Optional[QPoint] = None

        # Enable mouse tracking for rubber band
        self.setMouseTracking(True)

        # Set background
        self.setStyleSheet("background-color: #2b2b2b;")

        # Set minimum size
        self.setMinimumSize(400, 300)

    def set_image(self, qimage: QImage):
        """Set the image to display.

        Args:
            qimage: QImage to display.
        """
        self.qimage = qimage
        self.update()  # Trigger repaint

    def set_regions(self, regions: List[Region]):
        """Set the regions to display as overlays.

        Args:
            regions: List of Region objects to draw.
        """
        self.regions = regions
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        """Paint the image and region overlays.

        Args:
            event: QPaintEvent.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw image if present
        if self.qimage:
            # Calculate scaling to fit image in widget while maintaining aspect ratio
            widget_rect = self.rect()
            image_rect = self.qimage.rect()

            # Calculate scale factor
            scale_x = widget_rect.width() / image_rect.width()
            scale_y = widget_rect.height() / image_rect.height()
            scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down

            # Calculate target size
            target_width = int(image_rect.width() * scale)
            target_height = int(image_rect.height() * scale)

            # Center the image
            x_offset = (widget_rect.width() - target_width) // 2
            y_offset = (widget_rect.height() - target_height) // 2

            # Draw the image
            target_rect = QRect(x_offset, y_offset, target_width, target_height)
            painter.drawImage(target_rect, self.qimage)

            # Store the image transform for region drawing
            self.image_offset = (x_offset, y_offset)
            self.image_scale = scale

            # Draw regions
            self._draw_regions(painter, x_offset, y_offset, scale)
        else:
            # No image - draw placeholder
            painter.setPen(QPen(QColor(150, 150, 150)))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No image loaded\n\nFile → Open Image to get started"
            )

        # Draw rubber band if actively drawing
        if self.drawing and self.draw_start and self.draw_current:
            painter.setPen(QPen(QColor(0, 200, 255), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(0, 200, 255, 30))

            rect = QRect(self.draw_start, self.draw_current).normalized()
            painter.drawRect(rect)

    def _draw_regions(self, painter: QPainter, x_offset: int, y_offset: int, scale: float):
        """Draw region overlays.

        Args:
            painter: QPainter to draw with.
            x_offset: X offset of the image.
            y_offset: Y offset of the image.
            scale: Scale factor of the image.
        """
        for region in self.regions:
            # Transform region coordinates to screen coordinates
            screen_x = int(region.x * scale + x_offset)
            screen_y = int(region.y * scale + y_offset)
            screen_w = int(region.w * scale)
            screen_h = int(region.h * scale)

            # Choose color based on selection state
            if region.selected:
                # Selected regions: semi-transparent red
                color = QColor(255, 0, 0, 80)
                border_color = QColor(255, 0, 0, 200)
            else:
                # Unselected regions: semi-transparent gray
                color = QColor(100, 100, 100, 70)
                border_color = QColor(100, 100, 100, 150)

            # Draw filled rectangle
            painter.fillRect(screen_x, screen_y, screen_w, screen_h, color)

            # Draw border
            painter.setPen(QPen(border_color, 2))
            painter.drawRect(screen_x, screen_y, screen_w, screen_h)

    def mousePressEvent(self, event):
        """Handle mouse press for starting manual region creation.

        Args:
            event: QMouseEvent.
        """
        if event.button() == Qt.MouseButton.LeftButton and self.qimage:
            self.drawing = True
            self.draw_start = event.pos()
            self.draw_current = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for updating rubber band.

        Args:
            event: QMouseEvent.
        """
        if self.drawing:
            self.draw_current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release for completing manual region.

        Args:
            event: QMouseEvent.
        """
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.draw_current = event.pos()

            # Create the rectangle
            if self.draw_start and self.draw_current:
                rect = QRect(self.draw_start, self.draw_current).normalized()

                # Only emit if rectangle is large enough (avoid accidental clicks)
                if rect.width() > 5 and rect.height() > 5:
                    # Convert screen coordinates back to image coordinates
                    if hasattr(self, 'image_offset') and hasattr(self, 'image_scale'):
                        x_offset, y_offset = self.image_offset
                        scale = self.image_scale

                        # Transform back to image coordinates
                        image_x = int((rect.x() - x_offset) / scale)
                        image_y = int((rect.y() - y_offset) / scale)
                        image_w = int(rect.width() / scale)
                        image_h = int(rect.height() / scale)

                        # Create QRect in image coordinates
                        image_rect = QRect(image_x, image_y, image_w, image_h)

                        # Emit signal
                        self.manualRegionCreated.emit(image_rect)

            # Reset drawing state
            self.draw_start = None
            self.draw_current = None
            self.update()
