"""
Mock agents and clients for testing
"""

import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class MockContextLintAgent:
    """Mock Context Lint Agent for testing"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.context_dir: Optional[Path] = None
        self.issues_found: list[Dict[str, Any]] = []
        self.documents_checked = 0

    def lint_document(self, doc_path: Path) -> list:
        """Mock document linting"""
        self.documents_checked += 1
        issues = []

        # Simulate finding issues based on filename
        if "invalid" in str(doc_path):
            issues.append(
                {
                    "file": str(doc_path),
                    "issue": "Missing document_type in metadata",
                    "severity": "error",
                }
            )

        self.issues_found.extend(issues)
        return issues

    def generate_report(self) -> Dict[str, Any]:
        """Generate lint report"""
        return {
            "documents_checked": self.documents_checked,
            "issues_found": len(self.issues_found),
            "issues": self.issues_found,
        }


class MockSigstoreClient:
    """Mock Sigstore client for testing signature verification"""

    def __init__(self, rekor_url: str = "https://rekor.sigstore.dev"):
        self.rekor_url = rekor_url
        self.signed_documents: Dict[str, Dict[str, Any]] = {}
        self.verification_log: list[Dict[str, Any]] = []

    def sign(self, file_path: str, identity: str) -> Dict[str, str]:
        """Mock document signing"""
        # Generate mock signature
        content_hash = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()
        signature_data = f"{content_hash}:{identity}:{datetime.utcnow().isoformat()}"
        signature = base64.b64encode(signature_data.encode()).decode()

        # Store for verification
        self.signed_documents[file_path] = {
            "signature": signature,
            "hash": content_hash,
            "identity": identity,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return {
            "artifact_hash": content_hash,
            "signature": signature,
            "certificate": f"-----BEGIN CERTIFICATE-----\\nMOCK_CERT_{content_hash[:8]}\\n-----END CERTIFICATE-----",
            "transparency_log_index": str(len(self.signed_documents)),
            "timestamp": datetime.utcnow().isoformat(),
            "identity": identity,
        }

    def verify(self, file_path: str, signature_data: Dict[str, str]) -> bool:
        """Mock signature verification"""
        try:
            # Check if document was tampered
            current_hash = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()

            if file_path in self.signed_documents:
                original_hash = self.signed_documents[file_path]["hash"]
                is_valid = current_hash == original_hash
            else:
                # Decode signature to check
                decoded = base64.b64decode(signature_data["signature"]).decode()
                original_hash = decoded.split(":")[0]
                is_valid = current_hash == original_hash

            self.verification_log.append(
                {
                    "file": file_path,
                    "valid": is_valid,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            return bool(is_valid)
        except Exception:
            return False

    def get_transparency_log_entry(self, index: int) -> Optional[Dict[str, Any]]:
        """Mock transparency log retrieval"""
        if 0 <= index < len(self.signed_documents):
            entries = list(self.signed_documents.values())
            entry = entries[index]
            return {
                "index": index,
                "artifact_hash": entry["hash"],
                "identity": entry["identity"],
                "timestamp": entry["timestamp"],
                "entry": entry,
            }
        return None
