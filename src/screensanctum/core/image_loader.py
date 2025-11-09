"""Image loading and processing utilities."""

from pathlib import Path
from typing import Union
import numpy as np
from PIL import Image


class ImageLoadError(Exception):
    """Custom exception raised when image loading fails."""

    pass


def load_image(path: Union[str, Path]) -> Image.Image:
    """Load an image from the given path using Pillow.

    Args:
        path: Path to the image file (string or Path object).

    Returns:
        PIL Image object in RGB or RGBA format.

    Raises:
        ImageLoadError: If the image cannot be loaded or doesn't exist.
    """
    try:
        path = Path(path)
        if not path.exists():
            raise ImageLoadError(f"Image file not found: {path}")

        if not path.is_file():
            raise ImageLoadError(f"Path is not a file: {path}")

        # Open the image
        img = Image.open(path)

        # Normalize to RGB or RGBA
        if img.mode not in ('RGB', 'RGBA'):
            # Convert to RGB for most cases
            if img.mode == 'P':  # Palette mode
                img = img.convert('RGBA' if 'transparency' in img.info else 'RGB')
            elif img.mode in ('L', 'LA'):  # Grayscale
                img = img.convert('RGBA' if img.mode == 'LA' else 'RGB')
            elif img.mode == '1':  # Binary
                img = img.convert('RGB')
            elif img.mode in ('CMYK', 'LAB', 'YCbCr'):
                img = img.convert('RGB')
            else:
                # For any other mode, try to convert to RGB
                img = img.convert('RGB')

        return img

    except (IOError, OSError) as e:
        raise ImageLoadError(f"Failed to load image {path}: {str(e)}") from e
    except Exception as e:
        raise ImageLoadError(f"Unexpected error loading image {path}: {str(e)}") from e


def to_ocr_array(image: Image.Image) -> np.ndarray:
    """Convert a PIL Image to a NumPy array for OpenCV/Pytesseract processing.

    Args:
        image: PIL Image object.

    Returns:
        NumPy array in RGB format (H, W, 3) suitable for OCR processing.
    """
    # Convert to RGB if not already (remove alpha channel if present)
    if image.mode == 'RGBA':
        # Create a white background and paste the RGBA image on it
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # Convert to NumPy array
    arr = np.array(image)

    return arr
