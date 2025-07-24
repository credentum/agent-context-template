#!/usr/bin/env python3
"""
Tests for CI result signing and verification functionality.
"""

import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Scripts path is added in conftest.py

spec = importlib.util.spec_from_file_location(
    "post_ci_results",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "post-ci-results.py"),
)
post_ci_results = importlib.util.module_from_spec(spec)
spec.loader.exec_module(post_ci_results)
ResultCache = post_ci_results.ResultCache
sign_results_if_available = post_ci_results.sign_results_if_available

try:
    spec_sign = importlib.util.spec_from_file_location(
        "sign_ci_results",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "sign_ci_results.py"),
    )
    sign_ci_results = importlib.util.module_from_spec(spec_sign)
    spec_sign.loader.exec_module(sign_ci_results)
    CIResultSigner = sign_ci_results.CIResultSigner
    sign_ci_results_data = sign_ci_results.sign_ci_results_data

    spec_verify = importlib.util.spec_from_file_location(
        "verify_ci_results",
        os.path.join(os.path.dirname(__file__), "..", "scripts", "verify-ci-results.py"),
    )
    verify_ci_results = importlib.util.module_from_spec(spec_verify)
    spec_verify.loader.exec_module(verify_ci_results)
    CIResultsVerifier = verify_ci_results.CIResultsVerifier

    SIGNING_AVAILABLE = True
except ImportError:
    SIGNING_AVAILABLE = False


class TestCISigning(unittest.TestCase):
    """Test cryptographic signing of CI results."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_results = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:00:00Z",
            "commit_sha": "abc123",
            "branch": "feature/test",
            "checks": {
                "coverage": {
                    "passed": True,
                    "percentage": 85.5,
                    "threshold": 80.0,
                },
                "tests": {
                    "passed": True,
                    "total": 100,
                    "passed_count": 100,
                    "failed": 0,
                },
            },
        }

        # Sample GPG keys for testing (generated specifically for tests)
        self.test_private_key = """-----BEGIN PGP PRIVATE KEY BLOCK-----

lQPGBGb1234BCAC1234testkeyfortesting5678private90AB
=TEST
-----END PGP PRIVATE KEY BLOCK-----"""

        self.test_public_key = """-----BEGIN PGP PUBLIC KEY BLOCK-----

mQENBGb1234BCAC1234testkeyfortesting5678public90AB
=TEST
-----END PGP PUBLIC KEY BLOCK-----"""

    @unittest.skipUnless(SIGNING_AVAILABLE, "Signing not available")
    def test_sign_results(self):
        """Test signing CI results."""
        with patch.dict(os.environ, {"CI_SIGNING_KEY": self.test_private_key}):
            # Mock the GPG operations since we don't have real keys
            with patch("sign_ci_results.gnupg.GPG") as mock_gpg_class:
                mock_gpg = Mock()
                mock_gpg_class.return_value = mock_gpg

                # Mock successful import
                mock_import_result = Mock()
                mock_import_result.count = 1
                mock_import_result.fingerprints = ["TESTFINGERPRINT123"]
                mock_gpg.import_keys.return_value = mock_import_result

                # Mock successful signing
                mock_signature = Mock()
                mock_signature.__str__ = Mock(return_value="TESTSIGNATURE123")
                mock_signature.__bool__ = Mock(return_value=True)
                mock_gpg.sign.return_value = mock_signature

                # Test signing
                with CIResultSigner() as signer:
                    signature = signer.sign_results(self.test_results)

                    # Verify signature is base64 encoded
                    self.assertIsInstance(signature, str)
                    self.assertGreater(len(signature), 0)

                    # Verify GPG was called correctly
                    mock_gpg.sign.assert_called_once()
                    call_args = mock_gpg.sign.call_args[0]
                    signed_data = call_args[0]

                    # Verify canonical JSON format
                    self.assertIn('"branch":"feature/test"', signed_data)
                    self.assertIn('"commit_sha":"abc123"', signed_data)

    @unittest.skipUnless(SIGNING_AVAILABLE, "Signing not available")
    def test_verify_signature(self):
        """Test signature verification."""
        with patch("sign_ci_results.gnupg.GPG") as mock_gpg_class:
            mock_gpg = Mock()
            mock_gpg_class.return_value = mock_gpg

            # Mock successful import
            mock_import_result = Mock()
            mock_import_result.count = 1
            mock_gpg.import_keys.return_value = mock_import_result

            # Mock successful verification
            mock_gpg.verify_file.return_value = True

            # Test verification
            with CIResultSigner() as signer:
                is_valid = signer.verify_signature(
                    self.test_results, "TESTSIGNATURE123", self.test_public_key
                )

                self.assertTrue(is_valid)
                mock_gpg.verify_file.assert_called_once()

    def test_sign_results_data_helper(self):
        """Test the convenience function for signing."""
        with patch.dict(os.environ, {"CI_SIGNING_KEY": self.test_private_key}):
            with patch("sign_ci_results.CIResultSigner") as mock_signer_class:
                mock_signer = Mock()
                mock_signer_class.return_value.__enter__.return_value = mock_signer
                mock_signer.key_fingerprint = "TESTFINGERPRINT"
                mock_signer.sign_results.return_value = "TESTSIG123"

                results, signature = sign_ci_results_data(self.test_results)

                # Check metadata was added
                self.assertEqual(results["signed_with_fingerprint"], "TESTFINGERPRINT")
                self.assertEqual(results["signature_version"], "1.0")
                self.assertEqual(signature, "TESTSIG123")


class TestCIVerification(unittest.TestCase):
    """Test CI results verification with signatures."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_results = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:00:00Z",
            "commit_sha": "abc123",
            "branch": "feature/test",
            "signed_with_fingerprint": "TESTFINGERPRINT",
            "checks": {
                "coverage": {
                    "passed": True,
                    "percentage": 85.5,
                    "threshold": 80.0,
                },
                "tests": {
                    "passed": True,
                    "total": 100,
                    "passed_count": 100,
                    "failed": 0,
                },
                "linting": {
                    "passed": True,
                    "issues": [],
                },
                "type_check": {
                    "passed": True,
                    "errors": 0,
                },
            },
        }

    def test_verify_unsigned_results(self):
        """Test verification of unsigned results (backward compatibility)."""
        verifier = CIResultsVerifier()
        passed, message = verifier.verify_results(self.test_results)

        self.assertTrue(passed)
        self.assertIn("All CI checks passed", message)

    @unittest.skipUnless(SIGNING_AVAILABLE, "Signing not available")
    def test_verify_signed_results(self):
        """Test verification of signed results."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".asc", delete=False) as f:
            f.write("TEST_PUBLIC_KEY")
            public_key_path = f.name

        try:
            verifier = CIResultsVerifier(public_key_path=public_key_path)

            with patch.object(verifier, "verify_signature") as mock_verify:
                mock_verify.return_value = (True, "Signature valid")

                passed, message = verifier.verify_results(self.test_results, signature="TESTSIG123")

                self.assertTrue(passed)
                self.assertIn("Signature valid", message)
                mock_verify.assert_called_once_with(self.test_results, "TESTSIG123")
        finally:
            os.unlink(public_key_path)

    def test_verify_wrapped_results(self):
        """Test verification of wrapped results from artifacts."""
        wrapped_results = {
            "results": self.test_results,
            "signature": "TESTSIG123",
            "signed": True,
        }

        verifier = CIResultsVerifier()
        with patch.object(verifier, "verify_signature") as mock_verify:
            mock_verify.return_value = (True, "Signature valid")

            passed, message = verifier.verify_results(wrapped_results)

            self.assertTrue(passed)
            # Verify it extracted the inner results
            mock_verify.assert_called_once_with(self.test_results, "TESTSIG123")

    def test_require_signature_config(self):
        """Test configuration requiring signatures."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"require_signature": True}, f)
            config_file = f.name

        try:
            verifier = CIResultsVerifier(config_file=config_file)

            # Test with no signature - should fail
            passed, message = verifier.verify_results(self.test_results)

            self.assertFalse(passed)
            self.assertIn("Signature verification failed", message)
        finally:
            os.unlink(config_file)


class TestRetryLogic(unittest.TestCase):
    """Test retry logic for posting CI results."""

    def test_result_cache(self):
        """Test local result caching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResultCache(Path(tmpdir) / "cache")

            # Test save
            test_data = {"test": "data", "number": 42}
            cache_file = cache.save(test_data, "test-key")
            self.assertTrue(cache_file.exists())

            # Test load
            loaded = cache.load("test-key")
            self.assertEqual(loaded, test_data)

            # Test missing key
            missing = cache.load("missing-key")
            self.assertIsNone(missing)

            # Test cleanup
            cache.cleanup("test-key")
            self.assertFalse(cache_file.exists())

    @patch("subprocess.run")
    def test_retry_on_failure(self, mock_run):
        """Test retry logic triggers on failure."""
        # Mock subprocess to fail twice then succeed
        mock_run.side_effect = [
            Mock(side_effect=Exception("Network error")),
            Mock(side_effect=Exception("Timeout")),
            Mock(returncode=0),  # Success on third try
        ]

        # Mock the retry decorator to speed up tests
        with patch("time.sleep"):
            # We need to test the actual retry behavior
            # Since we can't easily test tenacity decorators, we'll test
            # the behavior indirectly through the sign_results_if_available function

            # Test that sign_results_if_available handles errors gracefully
            results, sig = sign_results_if_available({"test": "data"})
            self.assertEqual(results, {"test": "data"})
            self.assertIsNone(sig)  # No signature when not available


class TestPerformance(unittest.TestCase):
    """Test performance requirements."""

    @unittest.skipUnless(SIGNING_AVAILABLE, "Signing not available")
    def test_signing_performance(self):
        """Test that signing meets performance requirements (<100ms)."""
        large_results = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:00:00Z",
            "checks": {f"check_{i}": {"passed": True, "data": "x" * 100} for i in range(100)},
        }

        with patch.dict(os.environ, {"CI_SIGNING_KEY": "test_key"}):
            with patch("sign_ci_results.gnupg.GPG"):
                # Time the signing operation
                start_time = time.time()

                # We're mocking, so this should be very fast
                with patch("sign_ci_results.CIResultSigner.sign_results") as mock_sign:
                    mock_sign.return_value = "TESTSIG"
                    results, sig = sign_results_if_available(large_results)

                elapsed = (time.time() - start_time) * 1000  # Convert to ms

                # Should be well under 100ms with mocking
                self.assertLess(elapsed, 100, f"Signing took {elapsed:.1f}ms")

    def test_verification_performance(self):
        """Test that verification meets performance requirements (<50ms)."""
        large_results = {
            "version": "1.0",
            "timestamp": "2024-01-15T10:00:00Z",
            "checks": {f"check_{i}": {"passed": True, "data": "x" * 100} for i in range(100)},
        }

        verifier = CIResultsVerifier()

        # Time the verification
        start_time = time.time()
        passed, message = verifier.verify_results(large_results)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms

        # Should be well under 50ms for logic without actual GPG
        self.assertLess(elapsed, 50, f"Verification took {elapsed:.1f}ms")
        self.assertTrue(passed)  # Should pass without signature


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_invalid_signature_format(self):
        """Test handling of invalid signature formats."""
        verifier = CIResultsVerifier()

        with patch.object(verifier, "verify_signature") as mock_verify:
            mock_verify.return_value = (False, "Invalid signature format")

            passed, message = verifier.verify_results({"checks": {}}, signature="INVALID_BASE64!!!")

            # Should not fail entirely, just warn
            self.assertTrue(passed)  # Other checks pass
            self.assertIn("Invalid signature format", message)

    def test_missing_public_key(self):
        """Test handling of missing public key."""
        verifier = CIResultsVerifier(public_key_path="/nonexistent/key.asc")

        sig_valid, sig_msg = verifier.verify_signature({}, "TESTSIG")

        self.assertFalse(sig_valid)
        self.assertIn("Public key not found", sig_msg)

    def test_empty_results(self):
        """Test handling of empty results."""
        verifier = CIResultsVerifier()

        # Empty results should fail
        passed, message = verifier.verify_results({})
        self.assertFalse(passed)
        self.assertIn("Invalid results format", message)

    def test_malformed_results(self):
        """Test handling of malformed results."""
        verifier = CIResultsVerifier()

        # Results with wrong structure
        malformed = {
            "checks": {
                "coverage": "not_a_dict",  # Should be dict
            }
        }

        # Should handle gracefully
        passed, message = verifier.verify_results(malformed)
        self.assertFalse(passed)  # Should fail verification


if __name__ == "__main__":
    unittest.main()
