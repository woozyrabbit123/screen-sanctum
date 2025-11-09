"""Sensitive information detection."""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple, Optional, TYPE_CHECKING
import phonenumbers
from screensanctum.core.ocr import OcrToken

if TYPE_CHECKING:
    from screensanctum.core.config import TemplateIgnore, CustomRule


class PiiType(Enum):
    """Types of personally identifiable information that can be detected."""

    EMAIL = auto()
    IP = auto()
    DOMAIN = auto()
    URL = auto()
    PHONE = auto()
    FACE = auto()  # Stub for later face detection
    CUSTOM = auto()


@dataclass
class DetectedItem:
    """Represents a detected piece of sensitive information."""

    pii_type: PiiType
    text: str
    boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)  # (x, y, w, h)
    has_query_params: bool = False  # Specific for URLs


# Regex patterns for detection
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# IP address pattern with octet validation (0-255)
IP_PATTERN = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
)

# Domain pattern (excludes IPs and emails)
DOMAIN_PATTERN = re.compile(
    r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
)

# URL pattern with optional query parameters
URL_PATTERN = re.compile(
    r'\b(?:https?://|www\.)[^\s<>"\'\)]+',
    re.IGNORECASE
)


def _build_text_and_mapping(tokens: List[OcrToken]) -> Tuple[str, List[Optional[int]]]:
    """Build full text from tokens and create character-to-token mapping.

    Args:
        tokens: List of OCR tokens.

    Returns:
        Tuple of (full_text, char_to_token_map) where char_to_token_map[i]
        gives the token index for character i, or None for spaces.
    """
    full_text_parts = []
    char_to_token = []

    for token_idx, token in enumerate(tokens):
        # Add space if not the first token
        if full_text_parts:
            full_text_parts.append(' ')
            char_to_token.append(None)  # Space doesn't belong to any token

        # Add the token text
        full_text_parts.append(token.text)
        # Map each character in this token to the token index
        char_to_token.extend([token_idx] * len(token.text))

    full_text = ''.join(full_text_parts)
    return full_text, char_to_token


def _tokens_for_match(start: int, end: int, char_to_token: List[Optional[int]],
                      tokens: List[OcrToken]) -> List[Tuple[int, int, int, int]]:
    """Get bounding boxes for all tokens that contribute to a text match.

    Args:
        start: Start index of match in full text.
        end: End index of match in full text.
        char_to_token: Character-to-token mapping.
        tokens: List of OCR tokens.

    Returns:
        List of bounding boxes (x, y, w, h) for contributing tokens.
    """
    # Find unique token indices that contribute to this match
    token_indices = set()
    for i in range(start, end):
        if i < len(char_to_token) and char_to_token[i] is not None:
            token_indices.add(char_to_token[i])

    # Get bounding boxes for these tokens
    boxes = []
    for token_idx in sorted(token_indices):
        token = tokens[token_idx]
        boxes.append((token.x, token.y, token.w, token.h))

    return boxes


def _detect_emails(full_text: str, char_to_token: List[Optional[int]],
                   tokens: List[OcrToken], ignore_emails: List[str] = None,
                   ignore_domains: List[str] = None) -> List[DetectedItem]:
    """Detect email addresses in text.

    Args:
        full_text: Full text to search.
        char_to_token: Character-to-token mapping.
        tokens: List of OCR tokens.
        ignore_emails: List of emails to skip.
        ignore_domains: List of domains to skip.

    Returns:
        List of DetectedItem objects for emails.
    """
    if ignore_emails is None:
        ignore_emails = []
    if ignore_domains is None:
        ignore_domains = []

    items = []
    for match in EMAIL_PATTERN.finditer(full_text):
        email = match.group()

        # Check if email or its domain is in ignore list
        email_domain = email.split('@')[-1] if '@' in email else ''
        if email in ignore_emails or email_domain in ignore_domains:
            continue

        boxes = _tokens_for_match(match.start(), match.end(), char_to_token, tokens)
        if boxes:
            items.append(DetectedItem(
                pii_type=PiiType.EMAIL,
                text=email,
                boxes=boxes
            ))
    return items


def _detect_ips(full_text: str, char_to_token: List[Optional[int]],
                tokens: List[OcrToken]) -> List[DetectedItem]:
    """Detect IP addresses in text.

    Args:
        full_text: Full text to search.
        char_to_token: Character-to-token mapping.
        tokens: List of OCR tokens.

    Returns:
        List of DetectedItem objects for IPs.
    """
    items = []
    for match in IP_PATTERN.finditer(full_text):
        boxes = _tokens_for_match(match.start(), match.end(), char_to_token, tokens)
        if boxes:
            items.append(DetectedItem(
                pii_type=PiiType.IP,
                text=match.group(),
                boxes=boxes
            ))
    return items


def _detect_urls(full_text: str, char_to_token: List[Optional[int]],
                 tokens: List[OcrToken]) -> List[DetectedItem]:
    """Detect URLs in text.

    Args:
        full_text: Full text to search.
        char_to_token: Character-to-token mapping.
        tokens: List of OCR tokens.

    Returns:
        List of DetectedItem objects for URLs.
    """
    items = []
    for match in URL_PATTERN.finditer(full_text):
        url_text = match.group()
        has_query = '?' in url_text

        boxes = _tokens_for_match(match.start(), match.end(), char_to_token, tokens)
        if boxes:
            items.append(DetectedItem(
                pii_type=PiiType.URL,
                text=url_text,
                boxes=boxes,
                has_query_params=has_query
            ))
    return items


def _detect_domains(full_text: str, char_to_token: List[Optional[int]],
                    tokens: List[OcrToken], exclude_matches: List[DetectedItem],
                    ignore_domains: List[str] = None) -> List[DetectedItem]:
    """Detect domain names in text (excluding those already found in emails/URLs/IPs).

    Args:
        full_text: Full text to search.
        char_to_token: Character-to-token mapping.
        tokens: List[OcrToken].
        exclude_matches: List of already detected items to exclude.
        ignore_domains: List of domains to skip.

    Returns:
        List of DetectedItem objects for domains.
    """
    if ignore_domains is None:
        ignore_domains = []

    items = []

    # Build set of character ranges to exclude
    exclude_ranges = set()
    for item in exclude_matches:
        # Find this item's text in the full text
        for match in re.finditer(re.escape(item.text), full_text):
            for i in range(match.start(), match.end()):
                exclude_ranges.add(i)

    for match in DOMAIN_PATTERN.finditer(full_text):
        domain = match.group()

        # Check if this match overlaps with any excluded ranges
        overlaps = False
        for i in range(match.start(), match.end()):
            if i in exclude_ranges:
                overlaps = True
                break

        # Skip if domain is in ignore list
        if domain in ignore_domains:
            continue

        if not overlaps:
            boxes = _tokens_for_match(match.start(), match.end(), char_to_token, tokens)
            if boxes:
                items.append(DetectedItem(
                    pii_type=PiiType.DOMAIN,
                    text=domain,
                    boxes=boxes
                ))

    return items


def _detect_phones(full_text: str, char_to_token: List[Optional[int]],
                   tokens: List[OcrToken]) -> List[DetectedItem]:
    """Detect phone numbers using phonenumbers library.

    Args:
        full_text: Full text to search.
        char_to_token: Character-to-token mapping.
        tokens: List of OCR tokens.

    Returns:
        List of DetectedItem objects for phone numbers.
    """
    items = []
    seen = set()  # Track (text, start, end) to avoid duplicates from different regions

    # Try multiple regions for better detection
    # None means "generic" region
    for region in [None, 'US', 'GB', 'CA', 'AU']:
        try:
            for match in phonenumbers.PhoneNumberMatcher(full_text, region):
                phone_text = match.raw_string
                start = match.start
                end = match.end

                # Check if we've already seen this exact match (same text at same position)
                key = (phone_text, start, end)
                if key in seen:
                    continue
                seen.add(key)

                boxes = _tokens_for_match(start, end, char_to_token, tokens)
                if boxes:
                    items.append(DetectedItem(
                        pii_type=PiiType.PHONE,
                        text=phone_text,
                        boxes=boxes
                    ))
        except Exception:
            # phonenumbers can raise exceptions for certain inputs
            continue

    return items


def detect_pii(tokens: List[OcrToken], ignore_list: Optional["TemplateIgnore"] = None, custom_rules: Optional[List["CustomRule"]] = None) -> List[DetectedItem]:
    """Detect personally identifiable information from OCR tokens.

    This function:
    1. Builds full text from tokens
    2. Runs all detection methods
    3. Maps matches back to token bounding boxes
    4. Returns DetectedItem objects with all contributing boxes

    Args:
        tokens: List of OCR tokens.
        ignore_list: Optional TemplateIgnore object with domains/emails to skip in detection.
        custom_rules: Optional list of CustomRule objects for custom regex detection.

    Returns:
        List of DetectedItem objects containing detected PII.
    """
    if not tokens:
        return []

    # Extract ignore lists from template
    ignore_emails = []
    ignore_domains = []
    if ignore_list:
        ignore_emails = ignore_list.emails
        ignore_domains = ignore_list.domains

    # Build full text and character-to-token mapping
    full_text, char_to_token = _build_text_and_mapping(tokens)

    # Run all detections
    all_items = []

    # Detect emails
    all_items.extend(_detect_emails(full_text, char_to_token, tokens, ignore_emails, ignore_domains))

    # Detect IPs
    all_items.extend(_detect_ips(full_text, char_to_token, tokens))

    # Detect URLs
    all_items.extend(_detect_urls(full_text, char_to_token, tokens))

    # Detect domains (excluding emails, URLs, IPs)
    all_items.extend(_detect_domains(full_text, char_to_token, tokens, all_items, ignore_domains))

    # Detect phone numbers
    all_items.extend(_detect_phones(full_text, char_to_token, tokens))

    # Process Custom Rules
    if custom_rules:
        for rule in custom_rules:
            if not rule.name or not rule.regex:
                continue  # Skip invalid rules
            try:
                for match in re.finditer(rule.regex, full_text):
                    # Find tokens that contribute to this match
                    boxes = _tokens_for_match(match.start(), match.end(), char_to_token, tokens)
                    if not boxes:
                        continue

                    # Create a DetectedItem for this custom rule
                    item = DetectedItem(
                        pii_type=PiiType.CUSTOM,
                        text=rule.name,  # Use the rule's name, not the matched text
                        boxes=boxes
                    )
                    all_items.append(item)
            except re.error:
                pass  # Ignore invalid regex

    return all_items
