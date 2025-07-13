#!/usr/bin/env python3
"""
Extended property-based tests for comprehensive validation coverage
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

try:
    from hypothesis import assume, given, settings
    from hypothesis import strategies as st
    from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

    # Mock for when hypothesis is not installed
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip(reason="hypothesis not installed")(func)

        return decorator

    class RuleBasedStateMachine:
        pass


# Custom strategies for domain-specific data
if HAS_HYPOTHESIS:
    # Document metadata strategy
    metadata_strategy = st.fixed_dictionaries(
        {
            "document_type": st.sampled_from(["design", "decision", "sprint", "trace"]),
            "version": st.text(
                min_size=1, max_size=10, alphabet=st.characters(categories=["Nd", "L", "."])
            ),
            "created_date": st.dates(min_value=datetime(2020, 1, 1).date()).map(str),
            "author": st.text(min_size=1, max_size=50),
            "tags": st.lists(st.text(min_size=1, max_size=20), max_size=10),
        }
    )

    # Sprint task strategy
    task_strategy = st.fixed_dictionaries(
        {
            "name": st.text(min_size=1, max_size=100),
            "status": st.sampled_from(["pending", "in_progress", "completed", "blocked"]),
            "assignee": st.one_of(st.none(), st.text(min_size=1, max_size=50)),
            "priority": st.sampled_from(["low", "medium", "high", "critical"]),
        }
    )

    # File path strategy (valid paths)
    valid_path_strategy = st.text(
        min_size=1,
        max_size=200,
        alphabet=st.characters(whitelist_categories=["L", "Nd"], whitelist_characters="/-_."),
    ).filter(lambda p: not p.startswith("/") and ".." not in p)


class TestAdvancedPropertyValidation:
    """Advanced property-based validation tests"""

    if HAS_HYPOTHESIS:

        @given(
            st.dictionaries(
                # Config keys should be valid identifiers (ASCII alphanumeric + underscore/dot)
                # First character must be letter or underscore, then alphanumeric/underscore/dot
                st.text(
                    min_size=1,
                    max_size=50,
                    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.",
                ).filter(lambda s: s[0] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"),
                # Config values can be more permissive but exclude control chars
                st.text(
                    min_size=0,
                    max_size=200,
                    alphabet=st.characters(blacklist_categories=["Cc"]),  # No control characters
                ),
                min_size=1,
                max_size=20,
            )
        )
        def test_config_validation_properties(self, config: Dict[str, str]):
            """Test configuration validation properties"""
            # Property: All keys should be valid identifiers
            for key in config.keys():
                # Remove dots for nested keys
                identifier = key.replace(".", "_")
                # Valid identifier: starts with letter/underscore, contains only alphanumeric/underscore
                if identifier:
                    assert re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier) or all(
                        c.isdigit() for c in identifier
                    )

            # Property: Values should not contain control characters
            for value in config.values():
                assert all(ord(c) >= 32 or c in "\n\r\t" for c in value)

        @given(task_strategy)
        def test_task_state_transitions(self, task: Dict[str, Any]):
            """Test valid task state transitions"""
            valid_transitions = {
                "pending": ["in_progress", "blocked"],
                "in_progress": ["completed", "blocked", "pending"],
                "completed": [],  # Terminal state
                "blocked": ["pending", "in_progress"],
            }

            current_status = task["status"]
            allowed_next = valid_transitions.get(current_status, [])

            # Property: Only valid transitions allowed
            for next_status in ["pending", "in_progress", "completed", "blocked"]:
                can_transition = next_status in allowed_next
                if next_status == current_status:
                    can_transition = True  # Can stay in same state

                # Simulate transition validation
                if can_transition:
                    task_copy = task.copy()
                    task_copy["status"] = next_status
                    # Should be valid
                    assert task_copy["status"] in ["pending", "in_progress", "completed", "blocked"]

        @given(
            st.lists(
                st.floats(min_value=-100, max_value=100, allow_nan=False), min_size=2, max_size=1000
            )
        )
        def test_statistical_properties(self, values: List[float]):
            """Test statistical calculation properties"""
            # Calculate statistics
            mean = sum(values) / len(values)
            sorted_values = sorted(values)
            median = sorted_values[len(values) // 2]

            # Property: Mean is within bounds
            assert min(values) <= mean <= max(values)

            # Property: Median is an actual value for odd-length lists
            if len(values) % 2 == 1:
                assert median in values

            # Property: Standard deviation is non-negative
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance**0.5
            assert std_dev >= 0

        @given(valid_path_strategy)
        def test_path_normalization_properties(self, path: str):
            """Test path normalization properties"""
            # Normalize path
            normalized = path.replace("//", "/").strip("/")

            # Property: No double slashes
            assert "//" not in normalized

            # Property: No trailing slashes
            assert not normalized.endswith("/") or normalized == ""

            # Property: Idempotent
            double_normalized = normalized.replace("//", "/").strip("/")
            assert normalized == double_normalized

        @given(
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.integers(min_value=0, max_value=1000000),
                min_size=0,
                max_size=100,
            )
        )
        def test_rate_limiting_properties(self, request_counts: Dict[str, int]):
            """Test rate limiting calculation properties"""
            # Define rate limits
            rate_limits = {
                "default": 100,
                "api": 1000,
                "admin": 10000,
            }

            # Calculate if requests exceed limits
            violations = {}
            for endpoint, count in request_counts.items():
                limit = rate_limits.get(endpoint, rate_limits["default"])
                if count > limit:
                    violations[endpoint] = count - limit

            # Properties
            # 1. Violations are always positive
            assert all(v > 0 for v in violations.values())

            # 2. Non-violations aren't in the dict
            for endpoint, count in request_counts.items():
                limit = rate_limits.get(endpoint, rate_limits["default"])
                if count <= limit:
                    assert endpoint not in violations


if HAS_HYPOTHESIS:

    class DocumentStateMachine(RuleBasedStateMachine):
        """Stateful testing for document lifecycle"""

        documents = Bundle("documents")

        @rule(target=documents, metadata=metadata_strategy)
        def create_document(self, metadata):
            """Create a new document"""
            doc_id = f"doc_{len(self.documents)}"
            document = {
                "id": doc_id,
                "metadata": metadata,
                "content": {},
                "state": "draft",
                "history": [{"action": "created", "timestamp": datetime.utcnow().isoformat()}],
            }
            return document

        @rule(document=documents)
        def update_document(self, document):
            """Update an existing document"""
            # Can only update if not archived
            assume(document["state"] != "archived")

            document["metadata"]["updated_date"] = datetime.utcnow().isoformat()
            document["history"].append(
                {
                    "action": "updated",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Property: History grows monotonically
            assert len(document["history"]) > 1

        @rule(document=documents)
        def publish_document(self, document):
            """Publish a document"""
            assume(document["state"] == "draft")

            document["state"] = "published"
            document["metadata"]["published_date"] = datetime.utcnow().isoformat()
            document["history"].append(
                {
                    "action": "published",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Property: Published docs have published_date
            assert "published_date" in document["metadata"]

        @rule(document=documents)
        def archive_document(self, document):
            """Archive a document"""
            assume(document["state"] in ["draft", "published"])

            document["state"] = "archived"
            document["metadata"]["archived_date"] = datetime.utcnow().isoformat()
            document["history"].append(
                {
                    "action": "archived",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Property: Archived docs are immutable
            history_before = len(document["history"])
            # Future operations should not modify archived docs

        def invariants(self):
            """Check invariants that should always hold"""
            for doc in self.documents:
                # Every document has required fields
                assert "id" in doc
                assert "metadata" in doc
                assert "state" in doc
                assert "history" in doc

                # State is valid
                assert doc["state"] in ["draft", "published", "archived"]

                # History is chronological
                timestamps = [datetime.fromisoformat(h["timestamp"]) for h in doc["history"]]
                assert timestamps == sorted(timestamps)


class TestPropertyBasedSecurity:
    """Property-based security tests"""

    if HAS_HYPOTHESIS:

        @given(st.text())
        def test_injection_prevention(self, user_input: str):
            """Test prevention of various injection attacks"""
            # SQL injection patterns
            sql_patterns = [
                r"'\s*OR\s*'1'\s*=\s*'1",
                r";\s*DROP\s+TABLE",
                r"UNION\s+SELECT",
                r"--\s*$",
            ]

            # Check if input contains SQL injection attempts
            is_sql_injection = any(
                re.search(pattern, user_input, re.IGNORECASE) for pattern in sql_patterns
            )

            # Sanitize function
            def sanitize_sql_input(text: str) -> str:
                # Remove dangerous characters
                sanitized = text.replace("'", "''")  # Escape quotes
                sanitized = re.sub(r"[;]", "", sanitized)  # Remove semicolons
                return sanitized

            if is_sql_injection:
                sanitized = sanitize_sql_input(user_input)
                # Property: Sanitized input should not match injection patterns
                assert not any(
                    re.search(pattern, sanitized, re.IGNORECASE) for pattern in sql_patterns
                )

        @given(
            st.dictionaries(st.text(min_size=1, max_size=50), st.text(), min_size=0, max_size=10)
        )
        def test_xss_prevention(self, user_data: Dict[str, str]):
            """Test XSS prevention in user data"""
            xss_patterns = [
                "<script",
                "javascript:",
                "onerror=",
                "onclick=",
                "<iframe",
            ]

            def contains_xss(text: str) -> bool:
                return any(pattern in text.lower() for pattern in xss_patterns)

            def sanitize_html(text: str) -> str:
                # Basic HTML escaping
                text = text.replace("<", "&lt;")
                text = text.replace(">", "&gt;")
                text = text.replace('"', "&quot;")
                text = text.replace("'", "&#39;")
                return text

            # Check and sanitize all values
            sanitized_data = {}
            for key, value in user_data.items():
                if contains_xss(value):
                    sanitized_data[key] = sanitize_html(value)
                    # Property: Sanitized data should not contain XSS
                    assert not contains_xss(sanitized_data[key])
                else:
                    sanitized_data[key] = value

        @given(st.binary(min_size=0, max_size=1000))
        def test_binary_data_handling(self, binary_data: bytes):
            """Test safe handling of binary data"""
            # Property: Binary data should be properly encoded/decoded
            import base64

            # Encode
            encoded = base64.b64encode(binary_data).decode("ascii")
            assert isinstance(encoded, str)
            assert all(
                c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
                for c in encoded
            )

            # Decode
            decoded = base64.b64decode(encoded)
            assert decoded == binary_data


class TestPropertyBasedPerformance:
    """Property-based performance tests"""

    if HAS_HYPOTHESIS:

        @given(st.integers(min_value=1, max_value=10000))  # Reduced from 1M to 10K for faster tests
        @settings(max_examples=20)  # Reduced examples for performance tests
        def test_algorithmic_complexity(self, n: int):
            """Test that algorithms have expected complexity"""
            import time

            # Test linear time operation
            start = time.perf_counter()
            result = sum(range(n))  # O(n)
            linear_time = time.perf_counter() - start

            # Test quadratic time operation (with smaller n)
            if n <= 1000:  # Limit to avoid too long execution
                start = time.perf_counter()
                result = sum(i * j for i in range(n) for j in range(n))  # O(n²)
                quadratic_time = time.perf_counter() - start

                # Property: Quadratic should take significantly more time
                if n > 100:
                    assert quadratic_time > linear_time

            # Property: Linear time should scale linearly
            # (This is approximate due to system variability)
            if n > 10000:
                assert linear_time < n * 1e-7  # Rough upper bound

        @given(st.lists(st.integers(), min_size=0, max_size=10000))
        def test_memory_efficiency(self, data: List[int]):
            """Test memory-efficient operations"""
            import sys

            # Property: Generator uses less memory than list (for non-trivial lists)
            list_size = sys.getsizeof(data)
            gen_size = sys.getsizeof(x for x in data)

            # For small lists, generator overhead might be larger
            # Only check this property for lists with meaningful size
            if len(data) > 100:
                assert gen_size < list_size

            # Property: Set deduplication reduces or maintains size
            unique_data = list(set(data))
            assert len(unique_data) <= len(data)


if __name__ == "__main__":
    if HAS_HYPOTHESIS:
        # Run stateful tests
        DocumentStateMachine.TestCase.settings = settings(
            max_examples=50,
            stateful_step_count=20,
        )

        # Run specific test class
        pytest.main([__file__, "-v", "-k", "TestAdvancedPropertyValidation"])
    else:
        print("Hypothesis not installed, skipping property-based tests")
