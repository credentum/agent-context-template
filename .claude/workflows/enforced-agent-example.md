# Enforced Agent Execution Example

## How Sub-Agents Would Use Workflow Enforcement

### 1. Task Planner Agent (Phase 1)

```python
# At the start of task-planner agent execution
from workflow_validator import enforce_workflow_phase, complete_workflow_phase

# Enforce prerequisites
validator = enforce_workflow_phase(
    issue_number=1634,
    phase=1,
    agent_type="task-planner"
)

# Do the actual work
task_template = create_task_template(issue_1634)
scratchpad = create_scratchpad(issue_1634)

# Validate and record completion
complete_workflow_phase(
    validator=validator,
    phase=1,
    outputs={
        "task_template": "issue_1634_tasks.md",
        "scratchpad": "context/trace/scratchpad/2024-01-25-issue-1634.md",
        "time_estimate": "2 hours"
    }
)
```

### 2. Implementation Agent (Phase 2)

```python
# Would fail if Phase 1 not completed
validator = enforce_workflow_phase(
    issue_number=1634,
    phase=2,
    agent_type="main-claude"
)

# Implementation work...
implement_solution()

# Must pass validation
complete_workflow_phase(
    validator=validator,
    phase=2,
    outputs={
        "files_modified": ["context/schemas/*.yaml"],
        "commits": ["fix(context): refactor schemas"],
        "pre_commit_status": "passed"
    }
)
```

### 3. Test Runner Agent (Phase 3)

```python
# Would fail if no commits exist
validator = enforce_workflow_phase(
    issue_number=1634,
    phase=3,
    agent_type="test-runner"
)

# Run tests and CI
run_tests()
run_ci_locally()

# Record results
complete_workflow_phase(
    validator=validator,
    phase=3,
    outputs={
        "test_status": "passed",
        "coverage": "78.5%",
        "ci_status": "passed"
    }
)
```

## Workflow State File Example

The validator creates a state file `.workflow-state-1634.json`:

```json
{
  "issue_number": 1634,
  "current_phase": 3,
  "phases_completed": [
    {
      "phase": 1,
      "agent_type": "task-planner",
      "started_at": "2024-01-25T10:00:00",
      "completed_at": "2024-01-25T10:15:00",
      "status": "completed",
      "outputs": {
        "task_template": "issue_1634_tasks.md",
        "time_estimate": "2 hours"
      }
    },
    {
      "phase": 2,
      "agent_type": "main-claude",
      "started_at": "2024-01-25T10:16:00",
      "completed_at": "2024-01-25T10:45:00",
      "status": "completed",
      "outputs": {
        "files_modified": ["context/schemas/*.yaml"],
        "commits": ["fix(context): refactor schemas"],
        "pre_commit_status": "passed"
      }
    },
    {
      "phase": 3,
      "agent_type": "test-runner",
      "started_at": "2024-01-25T10:46:00",
      "status": "in_progress"
    }
  ],
  "created_at": "2024-01-25T10:00:00",
  "validation_errors": []
}
```

## Integration with Workflow Coordinator

The workflow coordinator would use this validator:

```python
class WorkflowCoordinator:
    def execute_workflow(self, issue_number: int):
        # Phase 1: Planning
        try:
            self.delegate_to_agent(
                agent_type="task-planner",
                prompt=f"Plan implementation for issue {issue_number}",
                phase=1,
                enforce_validation=True  # This triggers validator
            )
        except ValueError as e:
            print(f"Phase 1 failed: {e}")
            return

        # Phase 2: Implementation
        try:
            self.delegate_to_agent(
                agent_type="main-claude",
                prompt=f"Implement solution for issue {issue_number}",
                phase=2,
                enforce_validation=True
            )
        except ValueError as e:
            print(f"Phase 2 failed: {e}")
            return

        # Continue for all phases...
```

## Benefits of This Approach

1. **Automatic Validation** - Each phase validates prerequisites
2. **State Tracking** - Complete audit trail of execution
3. **Error Prevention** - Can't skip critical steps
4. **Clear Contracts** - Each agent knows requirements
5. **Resumable** - Can restart from any phase

## Validation Rules

### Phase 1 (Planning)
- **Prerequisites**: Issue must be accessible
- **Required Outputs**: Task template file must exist

### Phase 2 (Implementation)
- **Prerequisites**: Phase 1 completed, task template exists
- **Required Outputs**: Git commits, pre-commit passes

### Phase 3 (Testing)
- **Prerequisites**: Phase 2 completed, commits exist
- **Required Outputs**: Tests run, CI executed

### Phase 4 (PR Creation)
- **Prerequisites**: Phase 3 completed, CI passed
- **Required Outputs**: PR created and accessible

### Phase 5 (Monitoring)
- **Prerequisites**: Phase 4 completed, PR exists
- **Required Outputs**: Monitoring logs created

## Next Steps

1. Integrate validator into agent execution
2. Add more sophisticated validation rules
3. Create recovery mechanisms for failures
4. Add metrics and monitoring
5. Build UI for workflow visualization
