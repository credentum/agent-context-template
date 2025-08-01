# Workflow Issue Safe Command

Timeout-safe version of workflow-issue that executes phases individually.

## Usage

```bash
# Timeout-safe execution with phase-based runner
/workflow-issue-safe 123

# With hybrid mode
/workflow-issue-safe 123 --hybrid

# Resume if interrupted
/workflow-issue-safe 123 --resume
```

## Implementation

This command uses the phase-based runner to avoid timeouts:

```bash
# Execute from worktree (after worktree setup)
cd /workspaces/agent-context-template/worktree/issue-{issue_number}
python /workspaces/agent-context-template/scripts/workflow_phase_runner.py {issue_number} {options}
```

## Features

- **Automatic Phase Progression**: Executes phases one at a time
- **90-Second Phase Timeout**: Each phase runs within safe limits
- **State Persistence**: Saves progress between phases
- **Automatic Resume**: Can continue from last successful phase
- **No Full Workflow Timeout**: Avoids 2-minute limit issues

## Async Alternative

For background execution without blocking:

```bash
# Start in background
python /workspaces/agent-context-template/scripts/workflow_async_executor.py start 123 --hybrid

# Check status
python /workspaces/agent-context-template/scripts/workflow_async_executor.py status 123

# View logs
python /workspaces/agent-context-template/scripts/workflow_async_executor.py logs 123
```
