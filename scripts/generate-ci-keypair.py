#!/usr/bin/env python3
"""
Generate GPG keypair for CI result signing.

This utility creates a GPG keypair specifically for signing CI results,
exports the public key for repository storage, and provides instructions
for secure private key management.
"""

import argparse
import sys
import tempfile
from pathlib import Path

try:
    import gnupg
except ImportError:
    print("Error: python-gnupg not installed. Run: pip install python-gnupg")
    sys.exit(1)


def generate_keypair(name: str, email: str, comment: str = "CI Result Signing") -> tuple[str, str]:
    """
    Generate a GPG keypair for CI signing.

    Args:
        name: Real name for the key
        email: Email address for the key
        comment: Optional comment for the key

    Returns:
        Tuple of (fingerprint, key_id)
    """
    # Create temporary GPG home directory
    with tempfile.TemporaryDirectory() as gpg_home:
        gpg = gnupg.GPG(gnupghome=gpg_home)

        # Generate key with strong parameters
        input_data = gpg.gen_key_input(
            name_real=name,
            name_email=email,
            name_comment=comment,
            key_type="RSA",
            key_length=4096,
            key_usage="sign",
            expire_date="2y",  # 2 year expiration
            passphrase="",  # No passphrase for CI automation
        )

        print("Generating GPG keypair (this may take a moment)...")
        key = gpg.gen_key(input_data)

        if not key:
            print("Error: Failed to generate key")
            sys.exit(1)

        fingerprint = str(key)
        print(f"✓ Generated key with fingerprint: {fingerprint}")

        # Export public key
        public_key = gpg.export_keys(fingerprint)
        if not public_key:
            print("Error: Failed to export public key")
            sys.exit(1)

        # Export private key
        private_key = gpg.export_keys(fingerprint, secret=True)
        if not private_key:
            print("Error: Failed to export private key")
            sys.exit(1)

        return public_key, private_key, fingerprint


def save_keys(public_key: str, private_key: str, fingerprint: str, output_dir: Path) -> None:
    """Save keys to files with appropriate permissions."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save public key
    public_key_path = output_dir / "ci-public-key.asc"
    public_key_path.write_text(public_key)
    public_key_path.chmod(0o644)  # World readable
    print(f"✓ Saved public key to: {public_key_path}")

    # Save private key with restricted permissions
    private_key_path = output_dir / "ci-private-key.asc"
    private_key_path.write_text(private_key)
    private_key_path.chmod(0o600)  # Owner read/write only
    print(f"✓ Saved private key to: {private_key_path}")

    # Save fingerprint for reference
    fingerprint_path = output_dir / "key-fingerprint.txt"
    fingerprint_path.write_text(f"{fingerprint}\n")
    print(f"✓ Saved fingerprint to: {fingerprint_path}")


def print_instructions(output_dir: Path, fingerprint: str) -> None:
    """Print instructions for key management."""
    print("\n" + "=" * 70)
    print("CI SIGNING KEY SETUP INSTRUCTIONS")
    print("=" * 70)
    print("\n1. Add public key to repository:")
    print(f"   cp {output_dir}/ci-public-key.asc .github/ci-public-key.asc")
    print("   git add .github/ci-public-key.asc")
    print("   git commit -m 'feat(ci): add CI signing public key'")
    print("\n2. Add private key to CI environment:")
    print("   # For GitHub Actions:")
    print(f"   cat {output_dir}/ci-private-key.asc | base64 -w0 | pbcopy")
    print("   # Then add as secret CI_SIGNING_KEY in repository settings")
    print("\n3. Add fingerprint to CI environment:")
    print(f"   # Add as secret CI_KEY_FINGERPRINT: {fingerprint}")
    print("\n4. IMPORTANT: Secure the private key!")
    print("   # After adding to CI, securely delete local copy:")
    print(f"   shred -vfz {output_dir}/ci-private-key.asc")
    print("\n5. Test the setup:")
    print("   # Run a test CI execution with signing enabled")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Generate GPG keypair for CI result signing")
    parser.add_argument(
        "--name",
        default="CI Bot",
        help="Name for the GPG key (default: CI Bot)",
    )
    parser.add_argument(
        "--email",
        default="ci-bot@example.com",
        help="Email for the GPG key (default: ci-bot@example.com)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ci-keys"),
        help="Output directory for keys (default: ci-keys)",
    )
    args = parser.parse_args()

    # Generate keypair
    public_key, private_key, fingerprint = generate_keypair(args.name, args.email)

    # Save keys
    save_keys(public_key, private_key, fingerprint, args.output_dir)

    # Print instructions
    print_instructions(args.output_dir, fingerprint)


if __name__ == "__main__":
    main()
