"""Unit tests for PII detection functionality."""

import pytest
from screensanctum.core.ocr import OcrToken
from screensanctum.core.detection import PiiType, DetectedItem, detect_pii


def test_detect_email():
    """Test email detection from OCR tokens."""
    # Create tokens representing "Email: bob@example.com"
    tokens = [
        OcrToken(text="Email:", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="bob@example.com", x=60, y=0, w=150, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for emails
    emails = [item for item in results if item.pii_type == PiiType.EMAIL]

    # Should find exactly one email
    assert len(emails) == 1
    assert emails[0].text == "bob@example.com"
    assert len(emails[0].boxes) > 0
    # The email should be in the second token
    assert (60, 0, 150, 10) in emails[0].boxes


def test_detect_ip():
    """Test IP address detection with octet validation."""
    # Create tokens representing "Server IP: 192.168.1.1"
    tokens = [
        OcrToken(text="Server", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="IP:", x=60, y=0, w=30, h=10, conf=99),
        OcrToken(text="192.168.1.1", x=100, y=0, w=100, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for IPs
    ips = [item for item in results if item.pii_type == PiiType.IP]

    # Should find exactly one IP
    assert len(ips) == 1
    assert ips[0].text == "192.168.1.1"
    assert len(ips[0].boxes) > 0


def test_detect_invalid_ip():
    """Test that invalid IPs (octets > 255) are not detected."""
    # 256 is not a valid octet
    tokens = [
        OcrToken(text="Invalid:", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="192.168.1.256", x=60, y=0, w=120, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for IPs
    ips = [item for item in results if item.pii_type == PiiType.IP]

    # Should NOT find any valid IPs
    assert len(ips) == 0


def test_detect_phone():
    """Test phone number detection using phonenumbers library."""
    # Create tokens representing "Call: (555) 123-4567"
    tokens = [
        OcrToken(text="Call:", x=0, y=0, w=40, h=10, conf=99),
        OcrToken(text="(555)", x=50, y=0, w=50, h=10, conf=99),
        OcrToken(text="123-4567", x=110, y=0, w=80, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for phones
    phones = [item for item in results if item.pii_type == PiiType.PHONE]

    # Should find at least one phone number
    assert len(phones) >= 1
    # Check that we found the phone number (format may vary slightly)
    phone_texts = [p.text for p in phones]
    # The phonenumbers library might format it differently
    assert any("555" in text and "123" in text and "4567" in text for text in phone_texts)


def test_detect_multiple_phones():
    """Test that multiple instances of the same phone are detected separately.

    This is a critical bug fix: if "123-456-7890" appears twice in different
    locations, we should get TWO DetectedItems, not one.
    """
    # Create tokens with the same phone number appearing twice
    tokens = [
        OcrToken(text="First:", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="555-123-4567", x=60, y=0, w=100, h=10, conf=99),
        OcrToken(text="Second:", x=0, y=20, w=60, h=10, conf=99),
        OcrToken(text="555-123-4567", x=70, y=20, w=100, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for phones
    phones = [item for item in results if item.pii_type == PiiType.PHONE]

    # CRITICAL: Should find TWO phone numbers, not one
    # Even though the text is the same, they're at different positions
    assert len(phones) == 2, f"Expected 2 phone detections, got {len(phones)}"

    # Both should have the same text
    assert all("555" in p.text for p in phones)

    # But different bounding boxes
    boxes_set_1 = phones[0].boxes
    boxes_set_2 = phones[1].boxes
    # The boxes should be different (different y coordinates)
    assert boxes_set_1 != boxes_set_2


def test_detect_url_with_query_params():
    """Test URL detection and query parameter flag."""
    # Create tokens with a URL containing query parameters
    tokens = [
        OcrToken(text="Visit:", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="https://example.com?key=secret", x=60, y=0, w=250, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for URLs
    urls = [item for item in results if item.pii_type == PiiType.URL]

    # Should find exactly one URL
    assert len(urls) >= 1

    # Check that has_query_params is True
    url_with_params = [u for u in urls if u.has_query_params]
    assert len(url_with_params) >= 1


def test_detect_url_without_query_params():
    """Test URL detection without query parameters."""
    # Create tokens with a simple URL
    tokens = [
        OcrToken(text="Visit:", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="https://example.com", x=60, y=0, w=180, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for URLs
    urls = [item for item in results if item.pii_type == PiiType.URL]

    # Should find exactly one URL
    assert len(urls) >= 1

    # Check that has_query_params is False
    assert not urls[0].has_query_params


def test_detect_domain():
    """Test domain detection (not in email or URL)."""
    # Create tokens with a standalone domain
    tokens = [
        OcrToken(text="Domain:", x=0, y=0, w=60, h=10, conf=99),
        OcrToken(text="example.com", x=70, y=0, w=100, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Filter for domains
    domains = [item for item in results if item.pii_type == PiiType.DOMAIN]

    # Should find the domain
    assert len(domains) >= 1
    assert any("example.com" in d.text for d in domains)


def test_detect_mixed_pii():
    """Test detection of multiple PII types in one text."""
    # Create tokens with email, IP, and phone
    tokens = [
        OcrToken(text="Contact:", x=0, y=0, w=70, h=10, conf=99),
        OcrToken(text="admin@server.com", x=80, y=0, w=150, h=10, conf=99),
        OcrToken(text="IP:", x=0, y=20, w=30, h=10, conf=99),
        OcrToken(text="10.0.0.1", x=40, y=20, w=80, h=10, conf=99),
        OcrToken(text="Phone:", x=0, y=40, w=60, h=10, conf=99),
        OcrToken(text="555-1234", x=70, y=40, w=80, h=10, conf=99),
    ]

    # Run detection
    results = detect_pii(tokens)

    # Should find all three types
    pii_types = {item.pii_type for item in results}
    assert PiiType.EMAIL in pii_types
    assert PiiType.IP in pii_types
    assert PiiType.PHONE in pii_types


def test_empty_tokens():
    """Test that empty token list returns no detections."""
    results = detect_pii([])
    assert len(results) == 0


def test_no_pii_in_tokens():
    """Test that text without PII returns no detections."""
    tokens = [
        OcrToken(text="Hello", x=0, y=0, w=50, h=10, conf=99),
        OcrToken(text="world", x=60, y=0, w=50, h=10, conf=99),
    ]

    results = detect_pii(tokens)
    assert len(results) == 0
