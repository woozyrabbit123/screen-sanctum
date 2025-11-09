"""License validation functionality."""

import base64
import json
from dataclasses import dataclass
from datetime import datetime
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


# Hard-coded public key for license verification (ECDSA secp256r1)
# This public key corresponds to the private key used to sign licenses
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAED4uzqk+/bnoCobCmSjR9/HcLDyT5
TcrvIMTe7h1x8CqjtIBMV3HQrYJ3e8a+eYzzqa5n9QuEepfC56W+YJKfZg==
-----END PUBLIC KEY-----"""


def verify_license(raw_license_bytes: bytes) -> Optional[LicenseData]:
    """Verify a license using ECDSA signature verification.

    License format is:
        SIGNATURE_BASE64\nPAYLOAD_JSON

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

        # Load public key
        public_key = serialization.load_pem_public_key(
            PUBLIC_KEY_PEM.encode('utf-8')
        )

        # Verify signature
        payload_bytes = payload_json.encode('utf-8')
        try:
            public_key.verify(
                signature,
                payload_bytes,
                ec.ECDSA(hashes.SHA256())
            )
        except InvalidSignature:
            print("Invalid license signature")
            return None

        # Parse JSON payload
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON payload: {e}")
            return None

        # Extract license data
        email = payload.get('email')
        tier = payload.get('tier')
        issued_at_str = payload.get('issued_at')
        license_id = payload.get('license_id')

        if not all([email, tier, issued_at_str, license_id]):
            print("Missing required license fields")
            return None

        # Parse datetime
        try:
            issued_at = datetime.fromisoformat(issued_at_str)
        except ValueError as e:
            print(f"Invalid datetime format: {e}")
            return None

        # Create and return license data
        return LicenseData(
            email=email,
            tier=tier,
            issued_at=issued_at,
            license_id=license_id
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
        print("\nPUBLIC KEY (paste this into PUBLIC_KEY_PEM constant):")
        print(public_pem.decode('utf-8'))

    def sign_license(private_key_pem: str, email: str, tier: str):
        """Sign a license with the private key.

        Args:
            private_key_pem: Private key in PEM format.
            email: User's email address.
            tier: License tier (e.g., "pro").
        """
        print(f"\n=== Signing License for {email} ({tier}) ===\n")

        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None
        )

        # Create payload
        import uuid
        payload = {
            "email": email,
            "tier": tier,
            "issued_at": datetime.now().isoformat(),
            "license_id": str(uuid.uuid4())
        }

        # Serialize to JSON
        payload_json = json.dumps(payload, sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')

        # Sign
        signature = private_key.sign(
            payload_bytes,
            ec.ECDSA(hashes.SHA256())
        )

        # Encode signature as base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        # Create final license
        license_content = f"{signature_b64}\n{payload_json}"

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
            print(f"  ID: {verified.license_id}")
        else:
            print("✗ License verification failed!")

    # Command line interface
    if len(sys.argv) < 2:
        print("ScreenSanctum License Developer Tools")
        print("=" * 50)
        print("\nUsage:")
        print("  python -m screensanctum.licensing.license_check generate")
        print("  python -m screensanctum.licensing.license_check sign <email> <tier>")
        print("\nExamples:")
        print("  python -m screensanctum.licensing.license_check generate")
        print("  python -m screensanctum.licensing.license_check sign user@example.com pro")
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        generate_keypair()

    elif command == "sign":
        if len(sys.argv) < 4:
            print("Error: sign command requires email and tier")
            print("Usage: python -m screensanctum.licensing.license_check sign <email> <tier>")
            sys.exit(1)

        email = sys.argv[2]
        tier = sys.argv[3]

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
        sign_license(private_key_pem, email, tier)

    else:
        print(f"Unknown command: {command}")
        print("Valid commands: generate, sign")
        sys.exit(1)
