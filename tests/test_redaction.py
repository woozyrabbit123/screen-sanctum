"""Unit tests for image redaction functionality."""

import pytest
from PIL import Image
from screensanctum.core.regions import Region
from screensanctum.core.redaction import RedactionStyle, apply_redaction
from screensanctum.core.detection import PiiType


def test_redact_solid():
    """Test solid black rectangle redaction."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Create a region in the center
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=25,
        y=25,
        w=50,
        h=50,
        selected=True,
        manual=False
    )

    # Apply solid redaction
    redacted = apply_redaction(image, [region], RedactionStyle.SOLID)

    # Check that the center pixel is now black
    center_pixel = redacted.getpixel((50, 50))
    assert center_pixel == (0, 0, 0), f"Expected black (0, 0, 0), got {center_pixel}"

    # Check that a corner pixel is still white
    corner_pixel = redacted.getpixel((1, 1))
    assert corner_pixel == (255, 255, 255), f"Expected white (255, 255, 255), got {corner_pixel}"

    # Check original image is unchanged
    original_center = image.getpixel((50, 50))
    assert original_center == (255, 255, 255), "Original image should not be modified"


def test_redact_blur():
    """Test Gaussian blur redaction."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Draw a black square in the center to test blur
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 40, 60, 60], fill="black")

    # Create a region covering the black square
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=25,
        y=25,
        w=50,
        h=50,
        selected=True,
        manual=False
    )

    # Apply blur redaction
    redacted = apply_redaction(image, [region], RedactionStyle.BLUR)

    # The edges of the black square should now be blurred (gray values)
    # Check a pixel near the edge (should not be pure black or pure white)
    edge_pixel = redacted.getpixel((40, 50))
    # Should be grayish due to blur
    assert edge_pixel != (0, 0, 0), "Edge should be blurred, not pure black"
    assert edge_pixel != (255, 255, 255), "Edge should be blurred, not pure white"

    # Check that area outside redaction region is unchanged
    outside_pixel = redacted.getpixel((1, 1))
    assert outside_pixel == (255, 255, 255), "Outside region should be unchanged"


def test_redact_pixelate():
    """Test pixelation redaction."""
    # Create a 100x100 image with gradient for better pixelation testing
    image = Image.new("RGB", (100, 100), "white")

    # Draw some colored rectangles to test pixelation
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.rectangle([30, 30, 40, 40], fill="red")
    draw.rectangle([40, 40, 50, 50], fill="green")
    draw.rectangle([50, 50, 60, 60], fill="blue")

    # Create a region covering the colored area
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=25,
        y=25,
        w=50,
        h=50,
        selected=True,
        manual=False
    )

    # Apply pixelate redaction
    redacted = apply_redaction(image, [region], RedactionStyle.PIXELATE)

    # The pixelated region should not have the exact original colors
    # (due to downsampling/upsampling)
    # But it should still have some color variation
    center_pixel = redacted.getpixel((50, 50))

    # Center should not be pure white (since we had colored squares there)
    assert center_pixel != (255, 255, 255), "Pixelated region should show some effect"

    # Check that area outside redaction region is unchanged
    outside_pixel = redacted.getpixel((1, 1))
    assert outside_pixel == (255, 255, 255), "Outside region should be unchanged"


def test_redact_multiple_regions():
    """Test redacting multiple regions in one operation."""
    # Create a 200x100 white image
    image = Image.new("RGB", (200, 100), "white")

    # Create two regions
    region1 = Region(
        pii_type=PiiType.EMAIL,
        text="test1@example.com",
        x=10,
        y=10,
        w=40,
        h=40,
        selected=True,
        manual=False
    )

    region2 = Region(
        pii_type=PiiType.PHONE,
        text="555-1234",
        x=150,
        y=10,
        w=40,
        h=40,
        selected=True,
        manual=False
    )

    # Apply solid redaction to both
    redacted = apply_redaction(image, [region1, region2], RedactionStyle.SOLID)

    # Check both regions are redacted
    pixel1 = redacted.getpixel((30, 30))  # Center of region1
    pixel2 = redacted.getpixel((170, 30))  # Center of region2

    assert pixel1 == (0, 0, 0), "Region 1 should be black"
    assert pixel2 == (0, 0, 0), "Region 2 should be black"

    # Check middle area is still white
    middle_pixel = redacted.getpixel((100, 50))
    assert middle_pixel == (255, 255, 255), "Middle area should be white"


def test_redact_unselected_region():
    """Test that unselected regions are not redacted."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Create a region but mark it as NOT selected
    region = Region(
        pii_type=PiiType.EMAIL,
        text="test@example.com",
        x=25,
        y=25,
        w=50,
        h=50,
        selected=False,  # NOT selected
        manual=False
    )

    # Apply solid redaction
    redacted = apply_redaction(image, [region], RedactionStyle.SOLID)

    # Check that the center pixel is STILL WHITE (not redacted)
    center_pixel = redacted.getpixel((50, 50))
    assert center_pixel == (255, 255, 255), "Unselected region should not be redacted"


def test_redact_zero_size_region():
    """Test that zero-sized regions don't cause errors."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Create a zero-sized region
    region = Region(
        pii_type=None,
        text="invalid",
        x=50,
        y=50,
        w=0,  # Zero width
        h=0,  # Zero height
        selected=True,
        manual=False
    )

    # Should not raise an error
    redacted = apply_redaction(image, [region], RedactionStyle.SOLID)

    # Image should be unchanged
    assert redacted.getpixel((50, 50)) == (255, 255, 255)


def test_redact_out_of_bounds_region():
    """Test that regions outside image bounds are handled gracefully."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Create a region that's completely outside the image
    region = Region(
        pii_type=None,
        text="out of bounds",
        x=200,  # Outside image
        y=200,  # Outside image
        w=50,
        h=50,
        selected=True,
        manual=False
    )

    # Should not raise an error
    redacted = apply_redaction(image, [region], RedactionStyle.SOLID)

    # Image should be unchanged
    assert redacted.getpixel((50, 50)) == (255, 255, 255)


def test_redact_partial_bounds_region():
    """Test that regions partially outside bounds are clipped correctly."""
    # Create a 100x100 white image
    image = Image.new("RGB", (100, 100), "white")

    # Create a region that extends beyond the image bounds
    region = Region(
        pii_type=None,
        text="partial",
        x=75,
        y=75,
        w=50,  # Extends to x=125, which is out of bounds
        h=50,  # Extends to y=125, which is out of bounds
        selected=True,
        manual=False
    )

    # Should not raise an error and should redact the visible portion
    redacted = apply_redaction(image, [region], RedactionStyle.SOLID)

    # The visible portion should be redacted
    visible_pixel = redacted.getpixel((90, 90))
    assert visible_pixel == (0, 0, 0), "Visible portion should be redacted"

    # Corner should still be white
    corner_pixel = redacted.getpixel((1, 1))
    assert corner_pixel == (255, 255, 255)


def test_different_redaction_styles():
    """Test that different styles produce different results."""
    # Create a 100x100 white image with a colored square
    image = Image.new("RGB", (100, 100), "white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.rectangle([30, 30, 70, 70], fill="red")

    # Create a region
    region = Region(
        pii_type=None,
        text="test",
        x=25,
        y=25,
        w=50,
        h=50,
        selected=True,
        manual=False
    )

    # Apply each style
    solid = apply_redaction(image, [region], RedactionStyle.SOLID)
    blur = apply_redaction(image, [region], RedactionStyle.BLUR)
    pixelate = apply_redaction(image, [region], RedactionStyle.PIXELATE)

    # Get center pixel from each
    solid_pixel = solid.getpixel((50, 50))
    blur_pixel = blur.getpixel((50, 50))
    pixelate_pixel = pixelate.getpixel((50, 50))

    # Solid should be black
    assert solid_pixel == (0, 0, 0)

    # Blur and pixelate should be different from solid
    assert blur_pixel != solid_pixel, "Blur should differ from solid"
    assert pixelate_pixel != solid_pixel, "Pixelate should differ from solid"
