"""Image canvas widget for displaying and editing images with HiDPI support."""

from typing import Optional, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QPainter, QImage, QColor, QPen, QPixmap
from screensanctum.core.regions import Region


class ImageCanvas(QWidget):
    """Canvas widget for displaying and interacting with images.

    This widget properly handles HiDPI/Retina displays by maintaining
    separate coordinate spaces for source images and display.
    """

    # Signal emitted when user creates a manual region (in source image coordinates)
    manualRegionCreated = Signal(QRect)

    def __init__(self):
        """Initialize the image canvas."""
        super().__init__()

        # Image and regions state
        self.qimage: Optional[QImage] = None
        self.cached_pixmap: QPixmap | None = None
        self.regions: List[Region] = []

        # HiDPI/Retina coordinate tracking
        self.source_image_size: Optional[QSize] = None  # Original image size
        self.current_display_size: Optional[QSize] = None  # Actual display size
        self.display_offset: QPoint = QPoint(0, 0)  # Offset for centering
        self.scale_factor: float = 1.0  # Current scale factor

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
        if qimage:
            self.source_image_size = qimage.size()
            self.cached_pixmap = QPixmap.fromImage(qimage)
        else:
            self.source_image_size = None
            self.cached_pixmap = None
        self.update()  # Trigger repaint

    def set_regions(self, regions: List[Region]):
        """Set the regions to display as overlays.

        Args:
            regions: List of Region objects to draw.
        """
        self.regions = regions
        self.update()  # Trigger repaint

    def _map_point_to_source(self, display_point: QPoint) -> QPoint:
        """Map a display coordinate to source image coordinate.

        Args:
            display_point: Point in display/screen coordinates.

        Returns:
            Point in source image coordinates.
        """
        if not self.source_image_size or self.scale_factor == 0:
            return display_point

        # Remove offset
        adjusted_x = display_point.x() - self.display_offset.x()
        adjusted_y = display_point.y() - self.display_offset.y()

        # Scale back to source coordinates
        source_x = int(adjusted_x / self.scale_factor)
        source_y = int(adjusted_y / self.scale_factor)

        return QPoint(source_x, source_y)

    def _map_rect_from_source(self, source_rect: QRect) -> QRect:
        """Map a source image rectangle to display coordinates.

        Args:
            source_rect: Rectangle in source image coordinates (x, y, w, h).

        Returns:
            Rectangle in display/screen coordinates.
        """
        if not self.source_image_size or self.scale_factor == 0:
            return source_rect

        # Scale source coordinates to display
        display_x = int(source_rect.x() * self.scale_factor) + self.display_offset.x()
        display_y = int(source_rect.y() * self.scale_factor) + self.display_offset.y()
        display_w = int(source_rect.width() * self.scale_factor)
        display_h = int(source_rect.height() * self.scale_factor)

        return QRect(display_x, display_y, display_w, display_h)

    def paintEvent(self, event):
        """Paint the image and region overlays.

        Args:
            event: QPaintEvent.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw image if present
        if self.qimage and self.source_image_size:
            # Calculate scaling to fit image in widget while maintaining aspect ratio
            widget_rect = self.rect()

            # Calculate scale factor
            scale_x = widget_rect.width() / self.source_image_size.width()
            scale_y = widget_rect.height() / self.source_image_size.height()
            self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't scale up, only down

            # Calculate target display size
            target_width = int(self.source_image_size.width() * self.scale_factor)
            target_height = int(self.source_image_size.height() * self.scale_factor)
            self.current_display_size = QSize(target_width, target_height)

            # Center the image
            x_offset = (widget_rect.width() - target_width) // 2
            y_offset = (widget_rect.height() - target_height) // 2
            self.display_offset = QPoint(x_offset, y_offset)

            # Draw the image using cached pixmap for better performance
            target_rect = QRect(x_offset, y_offset, target_width, target_height)
            painter.drawPixmap(target_rect, self.cached_pixmap)

            # Draw regions using mapped coordinates
            self._draw_regions(painter)
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

    def _draw_regions(self, painter: QPainter):
        """Draw region overlays using proper coordinate mapping.

        Args:
            painter: QPainter to draw with.
        """
        for region in self.regions:
            # Create QRect in source coordinates
            source_rect = QRect(region.x, region.y, region.w, region.h)

            # Map to display coordinates
            display_rect = self._map_rect_from_source(source_rect)

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
            painter.fillRect(display_rect, color)

            # Draw border
            painter.setPen(QPen(border_color, 2))
            painter.drawRect(display_rect)

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

            # Only update the area we are drawing on (dirty rectangle optimization)
            if self.draw_start and self.draw_current:
                # Get the rectangle we are drawing
                rubber_band_rect = QRect(self.draw_start, self.draw_current).normalized()
                # Redraw *just* that rectangle (with a little padding)
                self.update(rubber_band_rect.adjusted(-5, -5, 5, 5))
            else:
                self.update()  # Fallback to full update

    def mouseReleaseEvent(self, event):
        """Handle mouse release for completing manual region.

        Args:
            event: QMouseEvent.
        """
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.draw_current = event.pos()

            # Create the rectangle in display coordinates
            if self.draw_start and self.draw_current:
                display_rect = QRect(self.draw_start, self.draw_current).normalized()

                # Only emit if rectangle is large enough (avoid accidental clicks)
                if display_rect.width() > 5 and display_rect.height() > 5:
                    # Map start and end points to source coordinates
                    source_start = self._map_point_to_source(display_rect.topLeft())
                    source_end = self._map_point_to_source(display_rect.bottomRight())

                    # Create rectangle in source coordinates
                    source_rect = QRect(source_start, source_end).normalized()

                    # Clamp to image bounds
                    if self.source_image_size:
                        source_rect = source_rect.intersected(
                            QRect(0, 0, self.source_image_size.width(), self.source_image_size.height())
                        )

                    # Emit signal with source coordinates
                    if source_rect.width() > 0 and source_rect.height() > 0:
                        self.manualRegionCreated.emit(source_rect)

            # Reset drawing state
            self.draw_start = None
            self.draw_current = None
            self.update()
