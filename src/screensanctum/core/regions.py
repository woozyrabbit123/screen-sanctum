"""Region management for image redaction."""

from dataclasses import dataclass
from typing import List, Optional
from screensanctum.core.detection import PiiType, DetectedItem


@dataclass
class Region:
    """Represents a rectangular region in an image to be redacted."""

    pii_type: Optional[PiiType]
    text: str
    x: int
    y: int
    w: int
    h: int
    selected: bool = True
    manual: bool = False


def merge_boxes(item: DetectedItem) -> Region:
    """Merge multiple bounding boxes from a DetectedItem into a single Region.

    Algorithm: Find the bounding rectangle that encompasses all boxes.
    - min_x: minimum x across all boxes
    - min_y: minimum y across all boxes
    - max_x: maximum (x + w) across all boxes
    - max_y: maximum (y + h) across all boxes

    Args:
        item: DetectedItem containing one or more bounding boxes.

    Returns:
        A Region object representing the merged bounding rectangle.
    """
    if not item.boxes:
        # Return a zero-sized region if no boxes
        return Region(
            pii_type=item.pii_type,
            text=item.text,
            x=0,
            y=0,
            w=0,
            h=0,
            selected=True,
            manual=False
        )

    # Find bounding rectangle
    min_x = min(box[0] for box in item.boxes)
    min_y = min(box[1] for box in item.boxes)
    max_x = max(box[0] + box[2] for box in item.boxes)
    max_y = max(box[1] + box[3] for box in item.boxes)

    return Region(
        pii_type=item.pii_type,
        text=item.text,
        x=min_x,
        y=min_y,
        w=max_x - min_x,
        h=max_y - min_y,
        selected=True,
        manual=False
    )


def build_regions(items: List[DetectedItem]) -> List[Region]:
    """Build regions from a list of detected items.

    Args:
        items: List of DetectedItem objects.

    Returns:
        List of Region objects, one per DetectedItem.
    """
    regions = []
    for item in items:
        region = merge_boxes(item)
        regions.append(region)
    return regions


def create_manual_region(x: int, y: int, w: int, h: int) -> Region:
    """Create a manual region (user-drawn).

    Args:
        x: X coordinate of the region.
        y: Y coordinate of the region.
        w: Width of the region.
        h: Height of the region.

    Returns:
        A Region object marked as manual.
    """
    return Region(
        pii_type=None,
        text="Manual Region",
        x=x,
        y=y,
        w=w,
        h=h,
        selected=True,
        manual=True
    )
