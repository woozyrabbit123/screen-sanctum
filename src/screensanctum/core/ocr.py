"""OCR functionality for text extraction from images."""

from dataclasses import dataclass
from typing import List
import numpy as np
import cv2
import pytesseract
from PIL import Image
from screensanctum.core.image_loader import to_ocr_array


@dataclass
class OcrToken:
    """Represents a single OCR token with its bounding box and confidence."""

    text: str
    x: int
    y: int
    w: int
    h: int
    conf: int


def run_ocr(image: Image.Image, conf_threshold: int = 60) -> List[OcrToken]:
    """Run OCR on an image and return tokens with bounding boxes.

    Args:
        image: PIL Image object to process.
        conf_threshold: Minimum confidence threshold (0-100). Default is 60.

    Returns:
        List of OcrToken objects containing text, position, and confidence.
    """
    # Convert PIL Image to NumPy array
    img_array = to_ocr_array(image)

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

    return tokens
