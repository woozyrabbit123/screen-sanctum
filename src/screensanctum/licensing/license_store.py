"""License storage and management."""

from pathlib import Path
from typing import Optional
import platformdirs


def get_license_path() -> Path:
    """Get the path to the license file.

    Returns:
        Path to license.dat file.
    """
    data_dir = Path(platformdirs.user_data_dir("ScreenSanctum", ensure_exists=True))
    return data_dir / "license.dat"


def load_license_file() -> Optional[bytes]:
    """Load the raw license file bytes.

    Returns:
        Raw license bytes if file exists, None otherwise.
    """
    license_path = get_license_path()

    if not license_path.exists():
        return None

    try:
        with open(license_path, "rb") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading license file: {e}")
        return None


def save_license_file(raw_bytes: bytes) -> bool:
    """Save raw license bytes to file.

    Args:
        raw_bytes: Raw license data to save.

    Returns:
        True if successful, False otherwise.
    """
    license_path = get_license_path()

    try:
        # Ensure parent directory exists
        license_path.parent.mkdir(parents=True, exist_ok=True)

        with open(license_path, "wb") as f:
            f.write(raw_bytes)
        return True
    except Exception as e:
        print(f"Error saving license file: {e}")
        return False


def delete_license_file() -> bool:
    """Delete the stored license file.

    Returns:
        True if successful, False otherwise.
    """
    license_path = get_license_path()

    try:
        if license_path.exists():
            license_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting license: {e}")
        return False
