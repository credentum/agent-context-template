#!/usr/bin/env python3
"""
Centralized configuration for workflow execution.
"""

import os

__all__ = ["WorkflowConfig"]


class WorkflowConfig:
    """Centralized configuration for workflow timeouts and settings."""

    # Configurable timeout per phase (can be overridden by env var)
    PHASE_TIMEOUT_SECONDS = int(os.environ.get("WORKFLOW_PHASE_TIMEOUT", "90"))

    # Default background process timeout
    BACKGROUND_PROCESS_TIMEOUT = int(os.environ.get("WORKFLOW_BACKGROUND_TIMEOUT", "300"))

    # Maximum number of retry attempts for failed operations
    MAX_RETRY_ATTEMPTS = int(os.environ.get("WORKFLOW_MAX_RETRIES", "3"))

    # Delay between retry attempts (seconds)
    RETRY_DELAY_SECONDS = int(os.environ.get("WORKFLOW_RETRY_DELAY", "5"))
    
    # Coverage baseline requirement (percentage)
    COVERAGE_BASELINE = float(os.environ.get("COVERAGE_BASELINE", "78.0"))
    
    # Coverage requirement for validators directory (percentage)
    VALIDATORS_COVERAGE_THRESHOLD = float(os.environ.get("VALIDATORS_COVERAGE_THRESHOLD", "90.0"))
