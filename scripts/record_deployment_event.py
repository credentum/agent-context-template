#!/usr/bin/env python3
"""
Record deployment event to KV store
Used by GitHub Actions workflow
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from context_kv import ContextKV
from datetime import datetime


def main():
    """Record deployment event"""
    branch = os.environ.get("GITHUB_REF_NAME", "unknown")
    commit = os.environ.get("GITHUB_SHA", "unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "unknown")

    kv = ContextKV()
    if kv.connect():
        success = kv.record_event(
            "deployment",
            data={
                "branch": branch,
                "commit": commit,
                "workflow": workflow,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        kv.close()

        if success:
            print(f"✓ Recorded deployment event for {branch} ({commit[:8]})")
            return 0
        else:
            print("✗ Failed to record deployment event", file=sys.stderr)
            return 1
    else:
        print("✗ Failed to connect to KV store", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
