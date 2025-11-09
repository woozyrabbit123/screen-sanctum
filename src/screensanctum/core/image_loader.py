"""Image loading and processing utilities."""

from pathlib import Path
from typing import Optional


class ImageLoader:
    """Handles loading and basic processing of images."""

    def __init__(self):
        """Initialize the image loader."""
        pass

    def load_image(self, path: Path) -> Optional[object]:
        """Load an image from the given path.

        Args:
            path: Path to the image file.

        Returns:
            Image object or None if loading fails.
        """
        # TODO: Implement image loading using Pillow
        pass

    def get_image_info(self, path: Path) -> dict:
        """Get metadata about an image.

        Args:
            path: Path to the image file.

        Returns:
            Dictionary containing image metadata.
        """
        # TODO: Implement metadata extraction
        pass
