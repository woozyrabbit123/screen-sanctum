"""Region management for image redaction."""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Region:
    """Represents a rectangular region in an image."""

    x: int
    y: int
    width: int
    height: int
    detection_type: str = "unknown"
    confidence: float = 1.0


class RegionManager:
    """Manages regions to be redacted in an image."""

    def __init__(self):
        """Initialize the region manager."""
        self.regions: List[Region] = []

    def add_region(self, region: Region) -> None:
        """Add a region to the manager.

        Args:
            region: Region to add.
        """
        self.regions.append(region)

    def remove_region(self, index: int) -> None:
        """Remove a region by index.

        Args:
            index: Index of the region to remove.
        """
        if 0 <= index < len(self.regions):
            del self.regions[index]

    def clear_regions(self) -> None:
        """Clear all regions."""
        self.regions.clear()

    def get_regions(self) -> List[Region]:
        """Get all regions.

        Returns:
            List of all regions.
        """
        return self.regions.copy()

    def merge_overlapping_regions(self) -> None:
        """Merge regions that overlap.

        TODO: Implement region merging logic.
        """
        pass
