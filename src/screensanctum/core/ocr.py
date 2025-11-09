"""OCR functionality for text extraction from images."""

import sys
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
import cv2
import pytesseract
from PIL import Image
from screensanctum.core.image_loader import to_ocr_array

# Maximum dimension for OCR processing to prevent memory issues with large images
MAX_OCR_DIMENSION = 3000


@dataclass
class OcrToken:
    """Represents a single OCR token with its bounding box and confidence."""

    text: str
    x: int
    y: int
    w: int
    h: int
    conf: int


def _get_tesseract_paths() -> Tuple[Optional[str], Optional[str]]:
    """Get Tesseract executable and tessdata paths.

    This function detects if the application is running as a PyInstaller bundle
    (frozen) and returns the appropriate paths for Tesseract.

    Returns:
        Tuple of (tesseract_cmd, tessdata_prefix):
        - tesseract_cmd: Path to tesseract executable
        - tessdata_prefix: Path to tessdata directory

    The function handles two scenarios:
    1. Frozen (PyInstaller bundle): Use bundled Tesseract from _MEIPASS
    2. Development: Use system-installed Tesseract
    """
    # Check if running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        # sys._MEIPASS is the temporary folder where PyInstaller extracts files
        base_path = sys._MEIPASS

        # Tesseract executable path (bundled in the package)
        # Windows: tesseract/tesseract.exe
        # Linux/Mac: tesseract/tesseract
        if sys.platform == 'win32':
            tess_cmd = os.path.join(base_path, 'tesseract', 'tesseract.exe')
        else:
            tess_cmd = os.path.join(base_path, 'tesseract', 'tesseract')

        # Tessdata directory (bundled language data)
        tessdata_prefix = os.path.join(base_path, 'tessdata')

        # Verify the bundled files exist
        if not os.path.exists(tess_cmd):
            print(f"Warning: Bundled Tesseract not found at {tess_cmd}")
            print("Falling back to system Tesseract...")
            tess_cmd = 'tesseract'  # Try system Tesseract
            tessdata_prefix = None

        return tess_cmd, tessdata_prefix
    else:
        # Running in development mode - use system Tesseract
        # pytesseract will use the default 'tesseract' command
        tess_cmd = 'tesseract'

        # Use environment variable if set, otherwise None (use Tesseract's default)
        tessdata_prefix = os.environ.get('TESSDATA_PREFIX')

        return tess_cmd, tessdata_prefix


def check_ocr_engine() -> bool:
    """Check if OCR engine (Tesseract) is available and working.

    This function verifies that Tesseract is properly installed and configured.
    It sets up the correct paths for both bundled (frozen) and development modes.

    Returns:
        True if Tesseract is available and working, False otherwise.
    """
    try:
        # Get the correct paths for Tesseract
        tess_cmd, tessdata_prefix = _get_tesseract_paths()

        # Set Tesseract executable path
        if tess_cmd:
            pytesseract.pytesseract.tesseract_cmd = tess_cmd

        # Set tessdata path if specified
        if tessdata_prefix:
            os.environ['TESSDATA_PREFIX'] = tessdata_prefix

        # Test Tesseract with a minimal image
        test_image = Image.new('RGB', (1, 1), color='white')
        pytesseract.image_to_string(test_image, timeout=5)

        return True

    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract OCR engine not found.")
        print("Please install Tesseract or ensure it's in your PATH.")
        return False

    except Exception as e:
        print(f"Error checking OCR engine: {e}")
        return False


def run_ocr(image: Image.Image, conf_threshold: int = 60) -> List[OcrToken]:
    """Run OCR on an image and return tokens with bounding boxes.

    This function automatically configures Tesseract paths for both
    bundled (PyInstaller) and development environments.

    Args:
        image: PIL Image object to process.
        conf_threshold: Minimum confidence threshold (0-100). Default is 60.

    Returns:
        List of OcrToken objects containing text, position, and confidence.

    Raises:
        pytesseract.TesseractNotFoundError: If Tesseract is not found.
    """
    # Configure Tesseract paths (handles both frozen and development modes)
    tess_cmd, tessdata_prefix = _get_tesseract_paths()

    # Set Tesseract executable path
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd

    # Set tessdata path if specified
    if tessdata_prefix:
        os.environ['TESSDATA_PREFIX'] = tessdata_prefix

    # Downsample large images to prevent memory issues
    # Create a copy for OCR
    image_copy = image.copy()
    scale_factor = 1.0

    if image_copy.width > MAX_OCR_DIMENSION or image_copy.height > MAX_OCR_DIMENSION:
        # Calculate the scale factor *before* thumbnailing
        original_size = image_copy.size
        image_copy.thumbnail((MAX_OCR_DIMENSION, MAX_OCR_DIMENSION), Image.Resampling.LANCZOS)
        new_size = image_copy.size

        # We will assume scaling is uniform, pick the width
        scale_factor = new_size[0] / original_size[0]

    # Run OCR on the (potentially) smaller copy
    img_array = to_ocr_array(image_copy)

    # Preprocess image for better OCR results
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Apply binary threshold
    # Using Otsu's method for automatic threshold calculation
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Run Tesseract OCR
    # output_type=Output.DICT returns a dictionary with keys:
    # 'text', 'left', 'top', 'width', 'height', 'conf', 'level', etc.
    ocr_data = pytesseract.image_to_data(
        binary,
        output_type=pytesseract.Output.DICT
    )

    # Parse OCR results and filter
    tokens = []
    n_boxes = len(ocr_data['text'])

    for i in range(n_boxes):
        text = ocr_data['text'][i]
        conf = int(ocr_data['conf'][i])

        # Filter out:
        # 1. Empty or whitespace-only text
        # 2. Confidence below threshold
        # 3. Invalid confidence values (pytesseract returns -1 for some items)
        if not text or text.isspace():
            continue
        if conf < conf_threshold:
            continue
        if conf == -1:  # Invalid confidence
            continue

        # Extract bounding box
        x = int(ocr_data['left'][i])
        y = int(ocr_data['top'][i])
        w = int(ocr_data['width'][i])
        h = int(ocr_data['height'][i])

        # Create token
        token = OcrToken(
            text=text,
            x=x,
            y=y,
            w=w,
            h=h,
            conf=conf
        )
        tokens.append(token)

    # Rescale tokens if we scaled the image
    if scale_factor != 1.0:
        rescaled_tokens = []
        for token in tokens:
            rescaled_tokens.append(
                OcrToken(
                    text=token.text,
                    x=int(token.x / scale_factor),
                    y=int(token.y / scale_factor),
                    w=int(token.w / scale_factor),
                    h=int(token.h / scale_factor),
                    conf=token.conf
                )
            )
        return rescaled_tokens  # Return the rescaled tokens

    return tokens  # Return the original tokens if no scaling happened
