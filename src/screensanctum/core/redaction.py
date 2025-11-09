"""Image redaction functionality."""

from enum import Enum, auto
from typing import List
from PIL import Image, ImageFilter, ImageDraw
from screensanctum.core.regions import Region


class RedactionStyle(Enum):
    """Redaction styles available for hiding sensitive information."""

    BLUR = auto()
    SOLID = auto()
    PIXELATE = auto()


def apply_redaction(image: Image.Image, regions: List[Region],
                    style: RedactionStyle = RedactionStyle.BLUR) -> Image.Image:
    """Apply redaction to specified regions in an image.

    Args:
        image: PIL Image object to redact.
        regions: List of Region objects to redact.
        style: RedactionStyle to use (BLUR, SOLID, or PIXELATE).

    Returns:
        New PIL Image object with redactions applied.
    """
    # Create a copy to avoid modifying the original
    result = image.copy()

    # Filter to only selected regions
    selected_regions = [r for r in regions if r.selected]

    for region in selected_regions:
        # Skip zero-sized regions
        if region.w <= 0 or region.h <= 0:
            continue

        # Ensure coordinates are within image bounds
        x = max(0, region.x)
        y = max(0, region.y)
        x2 = min(result.width, region.x + region.w)
        y2 = min(result.height, region.y + region.h)

        # Skip if region is completely outside image
        if x >= result.width or y >= result.height or x2 <= x or y2 <= y:
            continue

        if style == RedactionStyle.BLUR:
            result = _apply_blur(result, x, y, x2, y2)
        elif style == RedactionStyle.SOLID:
            result = _apply_solid(result, x, y, x2, y2)
        elif style == RedactionStyle.PIXELATE:
            result = _apply_pixelate(result, x, y, x2, y2)

    return result


def _apply_blur(image: Image.Image, x: int, y: int, x2: int, y2: int) -> Image.Image:
    """Apply Gaussian blur to a region.

    Args:
        image: PIL Image object.
        x, y: Top-left coordinates of the region.
        x2, y2: Bottom-right coordinates of the region.

    Returns:
        Image with blurred region.
    """
    # Extract the region
    region = image.crop((x, y, x2, y2))

    # Apply Gaussian blur
    blurred = region.filter(ImageFilter.GaussianBlur(radius=15))

    # Paste back
    result = image.copy()
    result.paste(blurred, (x, y))

    return result


def _apply_solid(image: Image.Image, x: int, y: int, x2: int, y2: int) -> Image.Image:
    """Apply solid black rectangle to a region.

    Args:
        image: PIL Image object.
        x, y: Top-left coordinates of the region.
        x2, y2: Bottom-right coordinates of the region.

    Returns:
        Image with solid black rectangle.
    """
    result = image.copy()
    draw = ImageDraw.Draw(result)

    # Draw solid black rectangle
    draw.rectangle([x, y, x2, y2], fill="black")

    return result


def _apply_pixelate(image: Image.Image, x: int, y: int, x2: int, y2: int,
                    pixel_size: int = 10) -> Image.Image:
    """Apply pixelation to a region.

    Algorithm:
    1. Extract region
    2. Downsample to very small size
    3. Upsample back to original size using nearest neighbor (no smoothing)

    Args:
        image: PIL Image object.
        x, y: Top-left coordinates of the region.
        x2, y2: Bottom-right coordinates of the region.
        pixel_size: Size of pixelation blocks. Default is 10.

    Returns:
        Image with pixelated region.
    """
    # Extract the region
    region = image.crop((x, y, x2, y2))

    # Calculate downsample size
    width = x2 - x
    height = y2 - y

    # Calculate new dimensions based on pixel_size
    small_width = max(1, width // pixel_size)
    small_height = max(1, height // pixel_size)

    # Downsample
    small = region.resize((small_width, small_height), Image.NEAREST)

    # Upsample back to original size
    pixelated = small.resize((width, height), Image.NEAREST)

    # Paste back
    result = image.copy()
    result.paste(pixelated, (x, y))

    return result
