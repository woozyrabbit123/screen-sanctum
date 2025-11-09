"""Utility functions for UI components."""

from PIL import Image
from PySide6.QtGui import QImage


def pil_to_qimage(pil_image: Image.Image) -> QImage:
    """Convert a PIL Image to QImage.

    Args:
        pil_image: PIL Image object.

    Returns:
        QImage object.
    """
    # Ensure image is in RGB or RGBA format
    if pil_image.mode == "RGBA":
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            QImage.Format.Format_RGBA8888
        )
    elif pil_image.mode == "RGB":
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            QImage.Format.Format_RGB888
        )
    else:
        # Convert to RGB first
        pil_image = pil_image.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data,
            pil_image.width,
            pil_image.height,
            QImage.Format.Format_RGB888
        )

    # Make a copy to avoid data corruption when PIL image is garbage collected
    return qimage.copy()
