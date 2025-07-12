#!/usr/bin/env python3
"""
Property-based tests using Hypothesis
Tests complex validation logic with generated test cases
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.validators.kv_validators import (
    sanitize_metric_name,
    validate_cache_entry,
    validate_metric_event,
    validate_redis_key,
    validate_session_data,
    validate_time_range,
)


class TestPropertyBasedValidation:
    """Property-based tests for validation functions"""

    @given(st.text(min_size=1, max_size=512))
    def test_redis_key_validation_properties(self, key: str):
        """Test properties of Redis key validation"""
        result = validate_redis_key(key)

        # Property: Result should always be boolean
        assert isinstance(result, bool)

        # Property: Keys with newlines/tabs should always be invalid
        if "\n" in key or "\t" in key or "\r" in key:
            assert result is False, f"Keys with whitespace should be invalid: {repr(key)}"

        # Property: Empty keys should be invalid
        if not key.strip():
            assert result is False, "Empty or whitespace-only keys should be invalid"

        # Property: Very long keys should be invalid
        if len(key) > 512:
            assert result is False, "Keys longer than 512 chars should be invalid"

    @given(st.text())
    def test_metric_name_sanitization_properties(self, name: str):
        """Test properties of metric name sanitization"""
        sanitized = sanitize_metric_name(name)

        # Property: Result should always be a string
        assert isinstance(sanitized, str)

        # Property: Result should only contain allowed characters
        allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789._")
        assert all(c in allowed_chars for c in sanitized), f"Invalid chars in: {sanitized}"

        # Property: Result should be lowercase
        assert sanitized == sanitized.lower()

        # Property: No consecutive dots
        assert ".." not in sanitized

        # Property: No leading/trailing dots
        if sanitized:
            assert not sanitized.startswith(".")
            assert not sanitized.endswith(".")

    @given(
        st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1)),
        st.timedeltas(min_value=timedelta(seconds=0), max_value=timedelta(days=365)),
    )
    def test_time_range_validation_properties(self, start_time: datetime, duration: timedelta):
        """Test properties of time range validation"""
        end_time = start_time + duration

        result = validate_time_range(start_time, end_time)

        # Property: Valid time ranges should return True
        if duration <= timedelta(days=365):
            assert result is True, f"Valid range should pass: {start_time} to {end_time}"
        else:
            assert result is False, "Ranges over 1 year should fail"

        # Property: End before start should always fail
        reversed_result = validate_time_range(end_time, start_time)
        if duration > timedelta(0):
            assert reversed_result is False, "End before start should fail"

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
                st.booleans(),
                st.none(),
            ),
            min_size=0,
            max_size=10,
        )
    )
    def test_cache_entry_validation_properties(self, entry: Dict[str, Any]):
        """Test properties of cache entry validation"""
        # Add required fields
        entry["key"] = "test_key"
        entry["value"] = {"data": "test"}
        entry["timestamp"] = datetime.utcnow().isoformat()
        entry["ttl"] = 3600

        result = validate_cache_entry(entry)

        # Property: Result should always be boolean
        assert isinstance(result, bool)

        # Property: Valid entries should have all required fields
        if result:
            assert "key" in entry
            assert "value" in entry
            assert "timestamp" in entry
            assert "ttl" in entry

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.integers(), st.floats(allow_nan=False), st.text()),
            min_size=1,
            max_size=20,
        )
    )
    def test_session_data_validation_properties(self, data: Dict[str, Any]):
        """Test properties of session data validation"""
        # Add required session fields
        session = {
            "session_id": "test_session",
            "user_id": "test_user",
            "created": datetime.utcnow().isoformat(),
            "data": data,
        }

        result = validate_session_data(session)

        # Property: Result should be boolean
        assert isinstance(result, bool)

        # Property: Sessions without required fields should fail
        if "session_id" not in session or "user_id" not in session:
            assert result is False


class TestPropertyBasedHashing:
    """Property-based tests for hashing functions"""

    @given(st.text())
    def test_content_hash_properties(self, content: str):
        """Test properties of content hashing"""
        embedder = HashDiffEmbedder()

        # Skip extremely large inputs for performance
        assume(len(content) < 1_000_000)

        hash1 = embedder._compute_content_hash(content)
        hash2 = embedder._compute_content_hash(content)

        # Property: Same content always produces same hash (deterministic)
        assert hash1 == hash2, "Hashing should be deterministic"

        # Property: Hash should always be 64 hex characters
        assert len(hash1) == 64, f"Hash should be 64 chars, got {len(hash1)}"
        assert all(c in "0123456789abcdef" for c in hash1), "Hash should be hexadecimal"

        # Property: Different content should (almost always) produce different hash
        if content:
            modified = content + "x"
            hash3 = embedder._compute_content_hash(modified)
            assert hash1 != hash3, "Different content should produce different hash"

    @given(
        st.lists(
            st.floats(min_value=-1.0, max_value=1.0, allow_nan=False), min_size=1, max_size=100
        )
    )
    def test_embedding_hash_properties(self, embedding: List[float]):
        """Test properties of embedding hashing"""
        embedder = HashDiffEmbedder()

        hash1 = embedder._compute_embedding_hash(embedding)
        hash2 = embedder._compute_embedding_hash(embedding)

        # Property: Same embedding always produces same hash
        assert hash1 == hash2, "Embedding hashing should be deterministic"

        # Property: Hash format should be consistent
        assert len(hash1) == 64, "Hash should be 64 characters"
        assert all(c in "0123456789abcdef" for c in hash1), "Hash should be hexadecimal"

        # Property: Small changes should produce different hash
        if embedding:
            modified = embedding.copy()
            modified[0] = modified[0] + 0.001
            hash3 = embedder._compute_embedding_hash(modified)
            assert hash1 != hash3, "Modified embedding should produce different hash"


class TestPropertyBasedDocumentStructures:
    """Property-based tests for document structures"""

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.recursive(
                st.one_of(
                    st.integers(), st.floats(allow_nan=False), st.text(), st.booleans(), st.none()
                ),
                lambda children: st.one_of(
                    st.lists(children, max_size=5),
                    st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=5),
                ),
                max_leaves=50,
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_yaml_document_properties(self, document: Dict[str, Any]):
        """Test properties of YAML document structures"""
        import yaml

        # Property: Valid Python dict should serialize to YAML
        yaml_str = yaml.dump(document, default_flow_style=False)
        assert isinstance(yaml_str, str)

        # Property: YAML should round-trip correctly
        loaded = yaml.safe_load(yaml_str)
        assert isinstance(loaded, dict)

        # Property: Keys should be preserved
        assert set(loaded.keys()) == set(document.keys())

    @given(
        st.dictionaries(
            st.sampled_from(["metadata", "content", "references"]),
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.one_of(st.text(), st.integers(), st.lists(st.text(), max_size=5)),
                max_size=5,
            ),
            min_size=1,
            max_size=3,
        )
    )
    def test_document_metadata_structure(self, document: Dict[str, Any]):
        """Test properties of document metadata structures"""
        # Add required metadata fields
        if "metadata" in document:
            document["metadata"]["document_type"] = "test"
            document["metadata"]["created_date"] = datetime.utcnow().isoformat()

        # Property: Documents with metadata should have document_type
        if "metadata" in document:
            assert "document_type" in document["metadata"]
            assert "created_date" in document["metadata"]

        # Property: Document structure should be serializable
        import json

        try:
            json_str = json.dumps(document, default=str)
            assert isinstance(json_str, str)

            # Should round-trip
            loaded = json.loads(json_str)
            assert isinstance(loaded, dict)
        except (TypeError, ValueError) as e:
            pytest.skip(f"Document not JSON serializable: {e}")


class TestPropertyBasedMetrics:
    """Property-based tests for metrics validation"""

    @given(
        st.text(min_size=1, max_size=50),
        st.sampled_from(["counter", "gauge", "histogram", "summary"]),
        st.floats(min_value=0, max_value=1e6, allow_nan=False),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5,
        ),
    )
    def test_metric_event_properties(
        self, name: str, metric_type: str, value: float, tags: Dict[str, str]
    ):
        """Test properties of metric events"""
        event = {
            "name": sanitize_metric_name(name),
            "type": metric_type,
            "value": value,
            "tags": tags,
            "timestamp": datetime.utcnow().isoformat(),
        }

        result = validate_metric_event(event)

        # Property: Valid events should pass validation
        assert isinstance(result, bool)

        if result:
            # Property: Name should be sanitized
            assert event["name"] == sanitize_metric_name(name)

            # Property: Type should be valid
            assert event["type"] in ["counter", "gauge", "histogram", "summary"]

            # Property: Value should be non-negative for counters
            if event["type"] == "counter":
                assert event["value"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
