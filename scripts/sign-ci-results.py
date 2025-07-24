#!/usr/bin/env python3
"""
Sign CI results with GPG for authenticity verification.

This module provides functionality to cryptographically sign CI results
using GPG, ensuring the integrity and authenticity of posted results.
"""

import base64
import json
import os
import sys
import tempfile
from typing import Optional

try:
    import gnupg
except ImportError:
    print("Error: python-gnupg not installed. Run: pip install python-gnupg")
    sys.exit(1)


class CIResultSigner:
    """Handles GPG signing of CI results."""

    def __init__(self, private_key: Optional[str] = None, fingerprint: Optional[str] = None):
        """
        Initialize the signer with GPG settings.

        Args:
            private_key: Base64-encoded private key or None to use from env
            fingerprint: Key fingerprint for verification or None to use from env
        """
        self.gpg_home = tempfile.mkdtemp()
        self.gpg = gnupg.GPG(gnupghome=self.gpg_home)

        # Get private key from parameter or environment
        key_data = private_key or os.environ.get("CI_SIGNING_KEY")
        if not key_data:
            raise ValueError("No private key provided. Set CI_SIGNING_KEY environment variable.")

        # Decode if base64 encoded
        try:
            # Try to decode as base64
            decoded_key = base64.b64decode(key_data).decode("utf-8")
            key_data = decoded_key
        except Exception:
            # Assume it's already decoded
            pass

        # Import private key
        import_result = self.gpg.import_keys(key_data)
        if not import_result.count:
            raise ValueError("Failed to import private key")

        self.key_fingerprint = fingerprint or os.environ.get("CI_KEY_FINGERPRINT")
        if not self.key_fingerprint:
            # Use the first imported key
            self.key_fingerprint = import_result.fingerprints[0]

        print(f"Initialized signer with key fingerprint: {self.key_fingerprint}")

    def sign_results(self, results: dict) -> str:
        """
        Sign CI results and return base64-encoded signature.

        Args:
            results: CI results dictionary to sign

        Returns:
            Base64-encoded detached signature
        """
        # Convert results to canonical JSON for consistent signing
        canonical_json = json.dumps(results, sort_keys=True, separators=(",", ":"))

        # Create detached signature
        signature = self.gpg.sign(
            canonical_json,
            keyid=self.key_fingerprint,
            detach=True,
            clearsign=False,
        )

        if not signature:
            raise RuntimeError("Failed to create signature")

        # Base64 encode for easy transport
        signature_b64 = base64.b64encode(str(signature).encode()).decode()
        return signature_b64

    def verify_signature(self, results: dict, signature_b64: str, public_key: str) -> bool:
        """
        Verify a signature against results using public key.

        Args:
            results: CI results dictionary
            signature_b64: Base64-encoded signature
            public_key: GPG public key

        Returns:
            True if signature is valid, False otherwise
        """
        # Import public key
        import_result = self.gpg.import_keys(public_key)
        if not import_result.count:
            print("Failed to import public key")
            return False

        # Decode signature
        try:
            signature = base64.b64decode(signature_b64).decode()
        except Exception as e:
            print(f"Failed to decode signature: {e}")
            return False

        # Convert results to canonical JSON (must match signing)
        canonical_json = json.dumps(results, sort_keys=True, separators=(",", ":"))

        # Create temporary files for verification
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as data_file:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sig") as sig_file:
                data_file.write(canonical_json)
                data_file.flush()
                sig_file.write(signature)
                sig_file.flush()

                # Verify signature
                verified = self.gpg.verify_file(sig_file.name, data_file.name)
                return bool(verified)

    def cleanup(self):
        """Clean up temporary GPG home directory."""
        import shutil

        if hasattr(self, "gpg_home") and os.path.exists(self.gpg_home):
            shutil.rmtree(self.gpg_home)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def sign_ci_results_data(results: dict) -> tuple[dict, str]:
    """
    Convenience function to sign CI results.

    Args:
        results: CI results dictionary

    Returns:
        Tuple of (results_with_metadata, signature)
    """
    with CIResultSigner() as signer:
        # Add signing metadata to results
        results_with_metadata = results.copy()
        results_with_metadata["signed_with_fingerprint"] = signer.key_fingerprint
        results_with_metadata["signature_version"] = "1.0"

        # Create signature
        signature = signer.sign_results(results_with_metadata)

        return results_with_metadata, signature


def main():
    """CLI interface for testing signing functionality."""
    import argparse

    parser = argparse.ArgumentParser(description="Sign CI results with GPG")
    parser.add_argument(
        "results_file",
        help="Path to CI results JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for signed results (default: stdout)",
    )
    parser.add_argument(
        "--verify",
        help="Verify signature instead of signing",
        action="store_true",
    )
    parser.add_argument(
        "--public-key",
        help="Path to public key file (for verification)",
    )
    parser.add_argument(
        "--signature",
        help="Signature to verify (base64 encoded)",
    )
    args = parser.parse_args()

    # Load results
    with open(args.results_file, "r") as f:
        results = json.load(f)

    if args.verify:
        # Verification mode
        if not args.public_key or not args.signature:
            print("Error: --public-key and --signature required for verification")
            sys.exit(1)

        with open(args.public_key, "r") as f:
            public_key = f.read()

        with CIResultSigner() as signer:
            is_valid = signer.verify_signature(results, args.signature, public_key)
            print(f"Signature valid: {is_valid}")
            sys.exit(0 if is_valid else 1)
    else:
        # Signing mode
        results_with_metadata, signature = sign_ci_results_data(results)

        output = {
            "results": results_with_metadata,
            "signature": signature,
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output, f, indent=2)
            print(f"Signed results saved to: {args.output}")
        else:
            print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
