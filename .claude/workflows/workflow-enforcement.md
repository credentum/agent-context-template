# Workflow Enforcement for Sub-Agents

## The Problem

Currently, there's no mechanism to ensure sub-agents follow the workflow correctly. Issues identified:

1. **No Validation Checkpoints** - Agents can skip steps without detection
2. **No State Tracking** - No way to verify previous phases completed
3. **No Error Recovery** - If an agent fails, the workflow breaks
4. **No Handoff Verification** - No guarantee that context is passed correctly

## Proposed Solutions

### 1. Workflow State Machine

Create a state tracking system that enforces phase transitions:

```yaml
# workflow-state.yaml
workflow_id: issue-1634
current_phase: 2
phases_completed:
  - phase: 0
    status: skipped
    reason: "Scope was clear"
  - phase: 1
    status: completed
    agent: task-planner
    outputs:
      - issue_1634_tasks.md
    validation_passed: true

required_outputs:
  phase_1:
    - task_template
    - time_estimate
  phase_2:
    - implementation_files
    - git_commits
  phase_3:
    - test_results
    - ci_status
```

### 2. Agent Contract System

Each agent must fulfill a contract:

```python
# agent_contracts.py
class WorkflowContract:
    def __init__(self, phase: int, agent_type: str):
        self.phase = phase
        self.agent_type = agent_type
        self.required_inputs = []
        self.required_outputs = []
        self.validation_rules = []

    def validate_inputs(self, inputs: dict) -> bool:
        """Verify agent receives required inputs from previous phase"""
        pass

    def validate_outputs(self, outputs: dict) -> bool:
        """Verify agent produces required outputs"""
        pass
```

### 3. Workflow Orchestrator

A coordinator that enforces the workflow:

```python
# workflow_orchestrator.py
class WorkflowOrchestrator:
    def __init__(self, workflow_def: str):
        self.workflow = load_workflow(workflow_def)
        self.state = WorkflowState()

    def execute_phase(self, phase: int) -> dict:
        # 1. Check prerequisites
        if not self.can_execute_phase(phase):
            raise WorkflowError(f"Prerequisites for phase {phase} not met")

        # 2. Load agent contract
        contract = self.get_phase_contract(phase)

        # 3. Prepare context for agent
        context = self.prepare_agent_context(phase)

        # 4. Execute with monitoring
        result = self.execute_with_monitoring(
            agent_type=contract.agent_type,
            context=context,
            timeout=contract.timeout
        )

        # 5. Validate outputs
        if not contract.validate_outputs(result):
            raise WorkflowError(f"Phase {phase} outputs invalid")

        # 6. Update state
        self.state.complete_phase(phase, result)

        return result
```

### 4. Validation Gates

Add explicit validation between phases:

```yaml
# validation-gates.yaml
gates:
  post_planning:
    checks:
      - file_exists: "issue_*_tasks.md"
      - file_contains:
          file: "issue_*_tasks.md"
          patterns: ["## Subtasks", "## Acceptance Criteria"]
      - git_status: "clean"

  pre_implementation:
    checks:
      - branch_exists: "fix/*"
      - ci_status: "passing"

  pre_pr:
    checks:
      - all_tests_pass: true
      - coverage_maintained: true
      - pre_commit_clean: true
```

### 5. Monitoring and Logging

Track every action for audit and debugging:

```yaml
# workflow-trace.yaml
workflow_id: issue-1634
trace:
  - timestamp: 2024-01-25T10:00:00Z
    phase: 1
    agent: task-planner
    action: started
    context_size: 15000

  - timestamp: 2024-01-25T10:15:00Z
    phase: 1
    agent: task-planner
    action: completed
    outputs_created:
      - issue_1634_tasks.md
    validation_status: passed
```

## Implementation Strategy

### Phase 1: Minimal Enforcement
1. Add workflow state file tracking
2. Create validation checkpoints
3. Add phase transition logging

### Phase 2: Contract System
1. Define agent contracts for each phase
2. Implement input/output validation
3. Add error recovery mechanisms

### Phase 3: Full Orchestration
1. Build workflow orchestrator
2. Add monitoring and metrics
3. Implement retry logic

## Example: Enforced Workflow Execution

```python
# Enhanced workflow command
def workflow_issue_enforced(issue_number: int):
    orchestrator = WorkflowOrchestrator('workflow-issue.yaml')

    try:
        # Phase 0: Investigation (optional)
        if orchestrator.needs_investigation(issue_number):
            result = orchestrator.execute_phase(0)

        # Phase 1: Planning (required)
        result = orchestrator.execute_phase(1)
        if not result.get('task_template'):
            raise WorkflowError("Planning phase must produce task template")

        # Phase 2: Implementation
        result = orchestrator.execute_phase(2)

        # Validation Gate
        if not orchestrator.validate_gate('pre_testing'):
            raise WorkflowError("Pre-testing validation failed")

        # Phase 3: Testing
        result = orchestrator.execute_phase(3)

        # Phase 4: PR Creation
        result = orchestrator.execute_phase(4)

        # Phase 5: Monitoring
        result = orchestrator.execute_phase(5)

    except WorkflowError as e:
        orchestrator.handle_error(e)
        raise
```

## Benefits

1. **Guaranteed Compliance** - Agents cannot skip required steps
2. **Clear Handoffs** - Each phase knows what it receives/produces
3. **Error Recovery** - Can resume from any phase
4. **Audit Trail** - Complete record of execution
5. **Quality Gates** - Prevent bad code from reaching PR

## Next Steps

1. Create workflow state tracking system
2. Define contracts for each agent type
3. Implement validation gates
4. Add monitoring and metrics
5. Update agents to use contracts
