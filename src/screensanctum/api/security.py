"""API security and authentication for ScreenSanctum."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from screensanctum.core.config import load_config

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key against configured keys.

    Args:
        api_key: The API key from the X-API-Key header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    config = load_config()
    if api_key in config.api_keys:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
