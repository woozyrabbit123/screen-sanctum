"""Unit tests for region management functionality."""

import pytest
from screensanctum.core.detection import PiiType, DetectedItem
from screensanctum.core.regions import Region, merge_boxes, build_regions, create_manual_region


def test_merge_boxes_single_box():
    """Test merging a DetectedItem with a single box."""
    # Create a DetectedItem with one box
    item = DetectedItem(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        boxes=[(10, 20, 100, 15)]  # (x, y, w, h)
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should have the same dimensions as the single box
    assert region.x == 10
    assert region.y == 20
    assert region.w == 100
    assert region.h == 15
    assert region.text == "test@example.com"
    assert region.pii_type == PiiType.EMAIL


def test_merge_boxes_multiple_contiguous():
    """Test merging multiple contiguous boxes."""
    # Create a DetectedItem with multiple boxes in a row
    item = DetectedItem(
        pii_type=PiiType.EMAIL,
        text="user@example.com",
        boxes=[
            (0, 0, 30, 10),    # "user"
            (35, 0, 10, 10),   # "@"
            (50, 0, 60, 10)    # "example.com"
        ]
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should create a bounding box that encompasses all three
    assert region.x == 0  # min x
    assert region.y == 0  # min y
    assert region.w == 110  # max x (50 + 60) - min x (0)
    assert region.h == 10  # max y (0 + 10) - min y (0)


def test_merge_boxes_multiple_non_contiguous():
    """Test merging multiple non-contiguous boxes (critical test)."""
    # Create a DetectedItem with boxes that have gaps between them
    # This simulates "bob @ example . com" where each part is a separate token
    item = DetectedItem(
        pii_type=PiiType.EMAIL,
        text="bob@example.com",
        boxes=[
            (0, 0, 10, 10),    # "bob" at x=0-10
            (20, 0, 10, 10),   # "@" at x=20-30 (gap from 10-20)
            (40, 0, 30, 10)    # "example.com" at x=40-70 (gap from 30-40)
        ]
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should create the TOTAL bounding box
    assert region.x == 0, "Should start at leftmost box"
    assert region.y == 0, "Should start at topmost box"
    assert region.w == 70, "Should span from x=0 to x=70 (0 to 40+30)"
    assert region.h == 10, "Height should cover all boxes"
    assert region.text == "bob@example.com"
    assert region.pii_type == PiiType.EMAIL


def test_merge_boxes_vertical_alignment():
    """Test merging boxes at different vertical positions."""
    # Create boxes that span multiple lines
    item = DetectedItem(
        pii_type=PiiType.PHONE,
        text="(555)\n123-4567",
        boxes=[
            (0, 0, 50, 10),    # First line at y=0
            (0, 15, 80, 10)    # Second line at y=15
        ]
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should encompass both lines
    assert region.x == 0  # Leftmost
    assert region.y == 0  # Topmost
    assert region.w == 80  # Width of widest box
    assert region.h == 25  # From y=0 to y=15+10=25


def test_merge_boxes_empty():
    """Test merging a DetectedItem with no boxes."""
    # Create an item with empty boxes list
    item = DetectedItem(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        boxes=[]  # Empty
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should return a zero-sized region
    assert region.w == 0
    assert region.h == 0
    assert region.text == "test@example.com"


def test_build_regions_single_item():
    """Test building regions from a single DetectedItem."""
    # Create a list with one item
    items = [
        DetectedItem(
            pii_type=PiiType.EMAIL,
            text="test@example.com",
            boxes=[(10, 20, 100, 15)]
        )
    ]

    # Build regions
    regions = build_regions(items)

    # Should have one region
    assert len(regions) == 1
    assert regions[0].x == 10
    assert regions[0].y == 20
    assert regions[0].text == "test@example.com"


def test_build_regions_multiple_items():
    """Test building regions from multiple DetectedItems."""
    # Create multiple items
    items = [
        DetectedItem(
            pii_type=PiiType.EMAIL,
            text="user1@example.com",
            boxes=[(0, 0, 100, 10)]
        ),
        DetectedItem(
            pii_type=PiiType.IP,
            text="192.168.1.1",
            boxes=[(0, 20, 80, 10)]
        ),
        DetectedItem(
            pii_type=PiiType.PHONE,
            text="555-1234",
            boxes=[(0, 40, 60, 10)]
        )
    ]

    # Build regions
    regions = build_regions(items)

    # Should have three regions
    assert len(regions) == 3

    # Check each region
    assert regions[0].pii_type == PiiType.EMAIL
    assert regions[1].pii_type == PiiType.IP
    assert regions[2].pii_type == PiiType.PHONE


def test_build_regions_empty_list():
    """Test building regions from an empty list."""
    regions = build_regions([])
    assert len(regions) == 0


def test_create_manual_region():
    """Test creating a manual (user-drawn) region."""
    # Create a manual region
    region = create_manual_region(x=10, y=20, w=100, h=50)

    # Check properties
    assert region.x == 10
    assert region.y == 20
    assert region.w == 100
    assert region.h == 50
    assert region.manual is True
    assert region.pii_type is None
    assert region.text == "Manual Region"
    assert region.selected is True


def test_region_dataclass():
    """Test Region dataclass properties."""
    # Create a region directly
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=0,
        y=0,
        w=100,
        h=20,
        selected=True,
        manual=False
    )

    # Check all properties
    assert region.pii_type == PiiType.EMAIL
    assert region.text == "test@example.com"
    assert region.x == 0
    assert region.y == 0
    assert region.w == 100
    assert region.h == 20
    assert region.selected is True
    assert region.manual is False


def test_region_selection_state():
    """Test toggling region selection state."""
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=0,
        y=0,
        w=100,
        h=20,
        selected=True,
        manual=False
    )

    # Toggle selection
    assert region.selected is True
    region.selected = False
    assert region.selected is False


def test_merge_boxes_complex_layout():
    """Test merging boxes in a complex 2D layout."""
    # Simulate a phone number that wraps across lines
    # "(555)" on line 1, "123-" on line 2, "4567" on line 3
    item = DetectedItem(
        pii_type=PiiType.PHONE,
        text="(555) 123-4567",
        boxes=[
            (100, 10, 40, 12),   # "(555)" at y=10
            (100, 25, 35, 12),   # "123-" at y=25
            (100, 40, 35, 12)    # "4567" at y=40
        ]
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should create a tall region covering all three lines
    assert region.x == 100
    assert region.y == 10  # Start at first line
    assert region.w == 40  # Width of widest token
    assert region.h == 42  # From y=10 to y=40+12=52, so height=42


def test_merge_boxes_overlapping():
    """Test merging overlapping boxes."""
    # Create boxes that overlap slightly
    item = DetectedItem(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        boxes=[
            (0, 0, 50, 10),
            (40, 0, 50, 10),  # Overlaps with previous box
            (80, 0, 30, 10)
        ]
    )

    # Merge boxes
    region = merge_boxes(item)

    # Should create bounding box covering all
    assert region.x == 0
    assert region.y == 0
    assert region.w == 110  # 80 + 30
    assert region.h == 10
