#!/usr/bin/env python3
"""
Sigstore signature verification tests
Tests document signing, verification, and tamper detection
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import yaml

from tests.mocks import MockSigstoreClient


class TestSigstoreIntegration:
    """Test Sigstore integration for document signing"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.context_dir = Path(self.temp_dir) / "context"
        self.context_dir.mkdir()

        self.sigstore_client = MockSigstoreClient()

    def teardown_method(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_document(self, filename: str, content: Dict[str, Any]) -> Path:
        """Create a test document"""
        doc_path = self.context_dir / filename
        with open(doc_path, "w") as f:
            yaml.dump(content, f)
        return doc_path

    def test_document_signing(self):
        """Test signing a document with Sigstore"""
        # Create document
        doc_content = {
            "metadata": {
                "document_type": "decision",
                "decision_id": "DEC-001",
                "created_date": "2024-01-15",
            },
            "title": "Critical architecture decision",
            "content": "Use microservices architecture",
        }

        doc_path = self.create_test_document("decision.yaml", doc_content)

        # Sign document
        signature = self.sigstore_client.sign(str(doc_path), identity="user@example.com")

        # Verify signature structure
        assert "artifact_hash" in signature
        assert "signature" in signature
        assert "certificate" in signature
        assert "timestamp" in signature
        assert "identity" in signature
        assert signature["identity"] == "user@example.com"

        # Save signature
        sig_path = doc_path.with_suffix(".yaml.sig")
        with open(sig_path, "w") as f:
            json.dump(signature, f, indent=2)

        assert sig_path.exists()

    def test_document_verification(self):
        """Test verifying a signed document"""
        # Create and sign document
        doc_content = {"metadata": {"document_type": "design"}, "content": "System design document"}

        doc_path = self.create_test_document("design.yaml", doc_content)
        signature = self.sigstore_client.sign(str(doc_path), "user@example.com")

        # Verify signature
        is_valid = self.sigstore_client.verify(str(doc_path), signature)
        assert is_valid is True

    def test_tampered_document_detection(self):
        """Test detection of tampered documents"""
        # Create and sign document
        doc_content = {
            "metadata": {"document_type": "sprint"},
            "sprint_number": 1,
            "status": "in_progress",
        }

        doc_path = self.create_test_document("sprint.yaml", doc_content)
        signature = self.sigstore_client.sign(str(doc_path), "user@example.com")

        # Tamper with document
        doc_content["status"] = "completed"  # Change status
        with open(doc_path, "w") as f:
            yaml.dump(doc_content, f)

        # Verify should fail
        is_valid = self.sigstore_client.verify(str(doc_path), signature)
        assert is_valid is False

    def test_signature_bundle_creation(self):
        """Test creating signature bundles for multiple documents"""
        # Create multiple documents
        documents = [
            ("doc1.yaml", {"type": "design", "content": "Design doc"}),
            ("doc2.yaml", {"type": "decision", "content": "Decision doc"}),
            ("doc3.yaml", {"type": "trace", "content": "Trace doc"}),
        ]

        signatures = {}

        for filename, content in documents:
            doc_path = self.create_test_document(filename, content)
            sig = self.sigstore_client.sign(str(doc_path), "bundler@example.com")
            signatures[filename] = sig

        # Create bundle
        bundle = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "signer": "bundler@example.com",
            "signatures": signatures,
            "manifest": {
                "total_documents": len(documents),
                "document_types": ["design", "decision", "trace"],
            },
        }

        bundle_path = self.context_dir / ".signatures" / "bundle.json"
        bundle_path.parent.mkdir(exist_ok=True)

        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2)

        assert bundle_path.exists()
        assert len(bundle["signatures"]) == 3

    def test_signature_expiration(self):
        """Test handling of expired signatures"""
        # Create document
        doc_path = self.create_test_document(
            "expiring.yaml", {"content": "Time-sensitive document"}
        )

        # Create signature with expiration
        signature = self.sigstore_client.sign(str(doc_path), "user@example.com")
        signature["expires_at"] = (datetime.utcnow() + timedelta(days=90)).isoformat()

        # Check if signature is expired
        expires_at = datetime.fromisoformat(signature["expires_at"])
        is_expired = datetime.utcnow() > expires_at

        assert is_expired is False

        # Simulate expired signature
        signature["expires_at"] = (datetime.utcnow() - timedelta(days=1)).isoformat()

        expires_at = datetime.fromisoformat(signature["expires_at"])
        is_expired = datetime.utcnow() > expires_at

        assert is_expired is True


class TestSigstoreWorkflow:
    """Test complete Sigstore workflow integration"""

    def test_ci_signing_workflow(self):
        """Test automated signing in CI/CD pipeline"""
        # Simulate CI environment
        ci_env = {
            "CI": "true",
            "GITHUB_ACTIONS": "true",
            "GITHUB_ACTOR": "github-actions[bot]",
            "GITHUB_SHA": "abc123def456",
            "GITHUB_REF": "refs/heads/main",
        }

        # Mock getting OIDC token (for documentation)
        _ = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."

        # Signing configuration
        signing_config = {
            "identity_provider": "github-actions",
            "fulcio_url": "https://fulcio.sigstore.dev",
            "rekor_url": "https://rekor.sigstore.dev",
            "identity": f"{ci_env['GITHUB_ACTOR']}@github",
        }

        # Verify CI identity
        assert signing_config["identity_provider"] == "github-actions"
        assert "@github" in signing_config["identity"]

    def test_verification_policy(self):
        """Test document verification policies"""
        # Define verification policies
        policies: dict[str, dict[str, Any]] = {
            "critical_documents": {
                "document_types": ["decision", "design"],
                "require_signature": True,
                "max_signature_age_days": 365,
                "trusted_signers": ["*@example.com", "ci-bot@github"],
            },
            "regular_documents": {
                "document_types": ["sprint", "trace"],
                "require_signature": False,
                "warn_if_unsigned": True,
            },
        }

        # Test policy application
        doc_type = "decision"

        # Find applicable policy
        applicable_policy = None
        for policy_name, policy in policies.items():
            document_types: list[str] = policy.get("document_types", [])
            if doc_type in document_types:
                applicable_policy = policy
                break

        assert applicable_policy is not None
        assert applicable_policy["require_signature"] is True
        assert applicable_policy["max_signature_age_days"] == 365

    def test_transparency_log_verification(self):
        """Test verification against transparency log"""
        sigstore = MockSigstoreClient()

        # Create and sign multiple documents
        for i in range(3):
            doc_path = Path(f"/tmp/doc{i}.yaml")
            with open(doc_path, "w") as f:
                yaml.dump({"id": i, "content": f"Document {i}"}, f)

            sigstore.sign(str(doc_path), f"user{i}@example.com")

        # Verify transparency log
        assert len(sigstore.transparency_log) == 3

        # Check log entry
        log_entry = sigstore.transparency_log[1]
        assert log_entry["index"] == 1
        assert log_entry["identity"] == "user1@example.com"
        assert "artifact_hash" in log_entry
        assert "timestamp" in log_entry

    def test_signature_metadata(self):
        """Test signature metadata and annotations"""
        # Create signature with metadata
        signature_metadata: dict[str, Any] = {
            "signature": "base64_signature_here",
            "certificate": "base64_certificate_here",
            "annotations": {
                "git.commit": "abc123",
                "git.branch": "main",
                "build.number": "42",
                "reviewer": "alice@example.com",
                "review_date": "2024-01-15",
            },
            "verification_metadata": {
                "verified_at": datetime.utcnow().isoformat(),
                "verified_by": "verification-service",
                "policy_version": "1.0",
            },
        }

        # Validate metadata
        assert "annotations" in signature_metadata
        annotations: dict[str, Any] = signature_metadata.get("annotations", {})
        git_branch: str = annotations.get("git.branch", "")
        assert git_branch == "main"
        assert "verification_metadata" in signature_metadata


class TestSigstoreRecovery:
    """Test recovery scenarios for signature verification"""

    def test_missing_signature_handling(self):
        """Test handling documents with missing signatures"""
        # Document without signature
        doc_info: dict[str, Any] = {
            "path": "context/docs/unsigned.yaml",
            "type": "design",
            "requires_signature": True,
        }

        # Check for signature file
        doc_path: str = str(doc_info.get("path", ""))
        sig_path = Path(doc_path + ".sig")
        has_signature = sig_path.exists()

        # Handle missing signature
        if not has_signature and doc_info["requires_signature"]:
            recovery_action: dict[str, Any] = {
                "action": "quarantine",
                "reason": "Missing required signature",
                "document": doc_info["path"],
                "suggested_remediation": [
                    "Request document owner to sign",
                    "Verify document integrity manually",
                    "Check if signature was accidentally deleted",
                ],
            }

            assert recovery_action["action"] == "quarantine"
            remediation: list[str] = recovery_action.get("suggested_remediation", [])
            assert isinstance(remediation, list) and len(remediation) > 0

    def test_signature_chain_validation(self):
        """Test validation of signature chains for document history"""
        # Document with version history
        doc_versions = [
            {
                "version": "1.0",
                "hash": "hash_v1",
                "signature": "sig_v1",
                "signer": "author@example.com",
                "timestamp": "2024-01-01T10:00:00Z",
            },
            {
                "version": "1.1",
                "hash": "hash_v1.1",
                "signature": "sig_v1.1",
                "signer": "reviewer@example.com",
                "timestamp": "2024-01-05T14:00:00Z",
                "previous_version_hash": "hash_v1",
            },
            {
                "version": "2.0",
                "hash": "hash_v2",
                "signature": "sig_v2",
                "signer": "author@example.com",
                "timestamp": "2024-01-10T09:00:00Z",
                "previous_version_hash": "hash_v1.1",
            },
        ]

        # Validate chain
        chain_valid = True
        for i in range(1, len(doc_versions)):
            current = doc_versions[i]
            previous = doc_versions[i - 1]

            # Check hash chain
            if current.get("previous_version_hash") != previous["hash"]:
                chain_valid = False
                break

            # Check timestamp ordering
            if current["timestamp"] <= previous["timestamp"]:
                chain_valid = False
                break

        assert chain_valid is True
