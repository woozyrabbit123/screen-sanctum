"""License validation functionality with enterprise-grade security."""

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from screensanctum.licensing.license_store import load_license_file


@dataclass
class LicenseData:
    """License data extracted from verified license."""

    email: str
    tier: str  # e.g., "pro"
    issued_at: datetime
    license_id: str
    exp: datetime  # Expiry timestamp
    nbf: datetime  # Not before timestamp
    kid: str  # Key ID for key rotation


# Public keys for license verification (key rotation support)
# Map of key_id -> public_key_pem
PUBLIC_KEYS = {
    "key-2025-01": """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED4uzqk+/bnoCobCmSjR9/HcLDyT5
TcrvIMTe7h1x8CqjtIBMV3HQrYJ3e8a+eYzzqa5n9QuEepfC56W+YJKfZg==
-----END PUBLIC KEY-----""",
}


def _canonicalize_payload(payload: dict) -> bytes:
    """Canonicalize payload to prevent signature bypass attacks.

    This function creates a canonical representation of the payload by:
    1. Sorting all keys
    2. Removing all whitespace
    3. Encoding to UTF-8

    Args:
        payload: Dictionary payload to canonicalize.

    Returns:
        Canonical byte representation of the payload.
    """
    # Sort keys and remove whitespace with separators
    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )
    return canonical_json.encode('utf-8')


def verify_license(raw_license_bytes: bytes) -> Optional[LicenseData]:
    """Verify a license using ECDSA signature verification.

    License format is:
        SIGNATURE_BASE64\nPAYLOAD_JSON

    This function performs:
    1. Signature verification using ECDSA
    2. Canonical JSON verification
    3. Time-based validation (nbf/exp with 5 min skew)
    4. Key rotation support via kid field

    Args:
        raw_license_bytes: Raw license file bytes.

    Returns:
        LicenseData if valid, None if invalid.
    """
    try:
        # Decode bytes to string
        license_text = raw_license_bytes.decode('utf-8')

        # Split into signature and payload
        parts = license_text.split('\n', 1)
        if len(parts) != 2:
            print("Invalid license format: missing signature or payload")
            return None

        signature_b64, payload_json = parts

        # Decode signature from base64
        try:
            signature = base64.b64decode(signature_b64)
        except Exception as e:
            print(f"Invalid base64 signature: {e}")
            return None

        # Parse JSON payload first to get kid
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON payload: {e}")
            return None

        # Get key ID for key rotation
        kid = payload.get('kid')
        if not kid:
            print("Missing key ID (kid) in payload")
            return None

        # Load correct public key based on kid
        public_key_pem = PUBLIC_KEYS.get(kid)
        if not public_key_pem:
            print(f"Unknown key ID: {kid}")
            return None

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8')
        )

        # Canonicalize payload for verification
        canonical_payload = _canonicalize_payload(payload)

        # Verify signature against canonical payload
        try:
            public_key.verify(
                signature,
                canonical_payload,
                ec.ECDSA(hashes.SHA256())
            )
        except InvalidSignature:
            print("Invalid license signature")
            return None

        # Extract required fields
        email = payload.get('email')
        tier = payload.get('tier')
        issued_at_str = payload.get('issued_at')
        license_id = payload.get('license_id')
        exp_str = payload.get('exp')
        nbf_str = payload.get('nbf')

        if not all([email, tier, issued_at_str, license_id, exp_str, nbf_str, kid]):
            print("Missing required license fields")
            return None

        # Parse datetimes
        try:
            issued_at = datetime.fromisoformat(issued_at_str)
            exp = datetime.fromisoformat(exp_str)
            nbf = datetime.fromisoformat(nbf_str)
        except ValueError as e:
            print(f"Invalid datetime format: {e}")
            return None

        # Time-based validation with 5 min skew tolerance
        now = datetime.utcnow()
        skew = timedelta(minutes=5)

        # Check not before (nbf)
        if now < (nbf - skew):
            print(f"License not yet valid (nbf: {nbf})")
            return None

        # Check expiry (exp)
        if now > (exp + skew):
            print(f"License expired (exp: {exp})")
            return None

        # Create and return license data
        return LicenseData(
            email=email,
            tier=tier,
            issued_at=issued_at,
            license_id=license_id,
            exp=exp,
            nbf=nbf,
            kid=kid
        )

    except Exception as e:
        print(f"Error verifying license: {e}")
        return None


def get_verified_license() -> Optional[LicenseData]:
    """Get verified license from stored license file.

    This is the main gate function for checking if the app is licensed.

    Returns:
        LicenseData if valid license exists, None otherwise.
    """
    raw = load_license_file()
    if not raw:
        return None

    return verify_license(raw)


# Developer tools for generating licenses
if __name__ == "__main__":
    import sys
    import uuid

    def generate_keypair():
        """Generate a new ECDSA keypair for license signing."""
        print("=== Generating ECDSA Keypair (secp256r1) ===\n")

        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1())

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        print("PRIVATE KEY (save this securely, DO NOT commit to git):")
        print(private_pem.decode('utf-8'))
        print("\nPUBLIC KEY (add this to PUBLIC_KEYS dict with a unique kid):")
        print(public_pem.decode('utf-8'))

    def sign_license(private_key_pem: str, email: str, tier: str, kid: str, days: int = 365):
        """Sign a license with the private key.

        Args:
            private_key_pem: Private key in PEM format.
            email: User's email address.
            tier: License tier (e.g., "pro").
            kid: Key ID (must match entry in PUBLIC_KEYS).
            days: License validity in days (default: 365).
        """
        print(f"\n=== Signing License for {email} ({tier}) ===\n")

        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )

        # Create payload with all required fields
        now = datetime.utcnow()
        payload = {
            "email": email,
            "tier": tier,
            "issued_at": now.isoformat(),
            "license_id": str(uuid.uuid4()),
            "nbf": now.isoformat(),  # Valid from now
            "exp": (now + timedelta(days=days)).isoformat(),  # Valid for specified days
            "kid": kid
        }

        # Canonicalize payload before signing
        canonical_payload = _canonicalize_payload(payload)

        # Sign canonical payload
        signature = private_key.sign(
            canonical_payload,
            ec.ECDSA(hashes.SHA256())
        )

        # Encode signature as base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        # Create final license (use canonical form for consistency)
        license_content = f"{signature_b64}\n{canonical_payload.decode('utf-8')}"

        print("LICENSE FILE CONTENT (save as license.dat):")
        print("=" * 60)
        print(license_content)
        print("=" * 60)

        # Also save to file
        with open("license.dat", "w") as f:
            f.write(license_content)
        print("\nSaved to license.dat")

        # Verify it works
        print("\nVerifying license...")
        verified = verify_license(license_content.encode('utf-8'))
        if verified:
            print(f"✓ License verified successfully!")
            print(f"  Email: {verified.email}")
            print(f"  Tier: {verified.tier}")
            print(f"  Issued: {verified.issued_at}")
            print(f"  Valid from: {verified.nbf}")
            print(f"  Expires: {verified.exp}")
            print(f"  Key ID: {verified.kid}")
            print(f"  License ID: {verified.license_id}")
        else:
            print("✗ License verification failed!")

    # Command line interface
    if len(sys.argv) < 2:
        print("ScreenSanctum License Developer Tools")
        print("=" * 50)
        print("\nUsage:")
        print("  python -m screensanctum.licensing.license_check generate")
        print("  python -m screensanctum.licensing.license_check sign <email> <tier> <kid> [days]")
        print("\nExamples:")
        print("  python -m screensanctum.licensing.license_check generate")
        print("  python -m screensanctum.licensing.license_check sign user@example.com pro key-2025-01")
        print("  python -m screensanctum.licensing.license_check sign user@example.com pro key-2025-01 30")
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        generate_keypair()

    elif command == "sign":
        if len(sys.argv) < 5:
            print("Error: sign command requires email, tier, and kid")
            print("Usage: python -m screensanctum.licensing.license_check sign <email> <tier> <kid> [days]")
            sys.exit(1)

        email = sys.argv[2]
        tier = sys.argv[3]
        kid = sys.argv[4]
        days = int(sys.argv[5]) if len(sys.argv) > 5 else 365

        # Verify kid exists in PUBLIC_KEYS
        if kid not in PUBLIC_KEYS:
            print(f"Warning: Key ID '{kid}' not found in PUBLIC_KEYS dict")
            print(f"Available keys: {', '.join(PUBLIC_KEYS.keys())}")
            print("License will be signed but may fail verification!")
            print()

        # Prompt for private key
        print("Paste your PRIVATE KEY (including BEGIN/END lines), then press Ctrl+D:")
        private_key_lines = []
        try:
            while True:
                line = input()
                private_key_lines.append(line)
        except EOFError:
            pass

        private_key_pem = '\n'.join(private_key_lines)
        sign_license(private_key_pem, email, tier, kid, days)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: generate, sign")
        sys.exit(1)
