"""Batch processor for processing multiple images with redaction templates."""

import os
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QObject, Signal
from PIL import Image

from screensanctum.core import image_loader, ocr, detection, regions, redaction
from screensanctum.core.config import RedactionTemplate


class BatchProcessor(QObject):
    """Batch processor for applying redaction templates to multiple images.

    This class is designed to run in a separate thread to prevent UI freezing.
    It processes all images in an input directory and saves redacted versions
    to an output directory.
    """

    # Signals
    progressUpdated = Signal(int, int)  # (current, total)
    fileProcessed = Signal(str, str)  # (filename, status)
    batchFinished = Signal(str)  # (summary message)

    # Supported image extensions
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}

    def __init__(self, parent=None):
        """Initialize the batch processor.

        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self.should_stop = False

    def stop(self):
        """Request to stop the batch processing."""
        self.should_stop = True

    def _find_images(self, input_dir: str, recursive: bool = True) -> List[Path]:
        """Find all supported images in the input directory.

        Args:
            input_dir: Directory to search for images.
            recursive: If True, search subdirectories recursively.

        Returns:
            List of Path objects for found images.
        """
        input_path = Path(input_dir)
        images = []

        if recursive:
            # Recursively find all images
            for ext in self.SUPPORTED_EXTENSIONS:
                images.extend(input_path.rglob(f'*{ext}'))
                images.extend(input_path.rglob(f'*{ext.upper()}'))
        else:
            # Only find images in the top-level directory
            for ext in self.SUPPORTED_EXTENSIONS:
                images.extend(input_path.glob(f'*{ext}'))
                images.extend(input_path.glob(f'*{ext.upper()}'))

        return sorted(images)

    def run_batch(self, input_dir: str, output_dir: str, template: RedactionTemplate, recursive: bool = True):
        """Run batch processing on all images in input_dir.

        This method is designed to be called from a worker thread.

        Args:
            input_dir: Directory containing images to process.
            output_dir: Directory to save redacted images.
            template: RedactionTemplate to use for processing.
            recursive: If True, process subdirectories recursively.
        """
        self.should_stop = False

        try:
            # Find all images
            images = self._find_images(input_dir, recursive)
            total_files = len(images)

            if total_files == 0:
                self.batchFinished.emit("No images found in input directory.")
                return

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            input_path = Path(input_dir)
            success_count = 0
            error_count = 0

            # Process each image
            for idx, image_path in enumerate(images):
                if self.should_stop:
                    self.batchFinished.emit(f"Batch stopped by user. {success_count} files processed, {error_count} errors.")
                    return

                # Emit progress
                self.progressUpdated.emit(idx + 1, total_files)

                # Get relative path to preserve folder structure
                try:
                    relative_path = image_path.relative_to(input_path)
                except ValueError:
                    # If relative_to fails, just use the filename
                    relative_path = Path(image_path.name)

                # Create output path preserving folder structure
                output_file = output_path / relative_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Process the image
                try:
                    # Load image
                    image = image_loader.load_image(str(image_path))

                    # Run OCR with template's confidence threshold
                    tokens = ocr.run_ocr(image, conf_threshold=template.ocr_conf)

                    # Run detection with template's ignore list
                    items = detection.detect_pii(tokens, template.ignore)

                    # Apply template policy to build regions
                    detected_regions = regions.apply_template_policy(items, template)

                    # Apply redaction using template's default style
                    redacted_image = redaction.apply_redaction(
                        image,
                        detected_regions,
                        template.style.default
                    )

                    # Save redacted image
                    # Use PNG format if template specifies, otherwise preserve original format
                    if template.export.format == "png":
                        output_file = output_file.with_suffix('.png')

                    redacted_image.save(str(output_file))

                    # Emit success
                    self.fileProcessed.emit(str(relative_path), "Success")
                    success_count += 1

                except image_loader.ImageLoadError as e:
                    self.fileProcessed.emit(str(relative_path), f"Error: {str(e)}")
                    error_count += 1

                except Exception as e:
                    # Catch all other errors (OCR, detection, etc.)
                    self.fileProcessed.emit(str(relative_path), f"Error: {str(e)}")
                    error_count += 1

            # Emit completion summary
            summary = f"Batch complete. {success_count} files processed successfully, {error_count} errors."
            self.batchFinished.emit(summary)

        except Exception as e:
            # Catch catastrophic errors
            self.batchFinished.emit(f"Batch failed: {str(e)}")
