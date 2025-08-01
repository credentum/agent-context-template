#!/usr/bin/env python3
"""Test script to validate state synchronization fix."""

import json
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from workflow_enforcer import WorkflowEnforcer
from workflow_phase_runner import PhaseRunner


def test_state_synchronization():
    """Test that PhaseRunner and WorkflowEnforcer share state properly."""
    test_issue = 99999  # Use a test issue number
    
    # Clean up any existing state files
    phase_state_file = Path(f".workflow-phase-state-{test_issue}.json")
    enforcer_state_file = Path(f".workflow-state-{test_issue}.json")
    
    if phase_state_file.exists():
        phase_state_file.unlink()
    if enforcer_state_file.exists():
        enforcer_state_file.unlink()
    
    print("🧪 Testing state synchronization between PhaseRunner and WorkflowEnforcer")
    print("=" * 60)
    
    # Test 1: PhaseRunner should use WorkflowEnforcer's state file
    runner = PhaseRunner(test_issue)
    print(f"✅ PhaseRunner state file: {runner.state_file}")
    print(f"✅ Expected: .workflow-state-{test_issue}.json")
    assert str(runner.state_file) == f".workflow-state-{test_issue}.json"
    
    # Test 2: Create some state via WorkflowEnforcer
    enforcer = WorkflowEnforcer(test_issue)
    
    # Mark investigation as completed
    enforcer.state["phases"]["investigation"] = {
        "phase_name": "investigation",
        "status": "completed",
        "started_at": "2025-01-01T10:00:00",
        "completed_at": "2025-01-01T10:30:00",
        "outputs": {"scope_clarity": True},
        "errors": [],
        "agent_type": "test"
    }
    enforcer._save_state()
    print("\n✅ Created test state via WorkflowEnforcer")
    
    # Test 3: PhaseRunner should load the state
    runner2 = PhaseRunner(test_issue)
    runner2._load_state()
    print(f"✅ PhaseRunner loaded {len(runner2.completed_phases)} completed phases")
    assert 0 in runner2.completed_phases  # investigation = phase 0
    
    # Test 4: Test skip_phases parameter in enforce_phase_entry
    can_proceed, message, _ = enforcer.enforce_phase_entry(
        "implementation",  # phase 2
        "test-agent",
        skip_phases=[1]  # Skip planning (phase 1)
    )
    print(f"\n✅ Enforcer allows implementation with skip_phases: {can_proceed}")
    print(f"   Message: {message}")
    assert can_proceed
    
    # Check that planning was marked as completed
    assert "planning" in enforcer.state["phases"]
    assert enforcer.state["phases"]["planning"]["status"] == "completed"
    print("✅ Planning phase was automatically marked as completed")
    
    # Clean up
    if enforcer_state_file.exists():
        enforcer_state_file.unlink()
    
    print("\n🎉 All tests passed! State synchronization is working correctly.")


if __name__ == "__main__":
    test_state_synchronization()