# Workflow Issue Command

Execute the complete issue-to-PR workflow with direct phase execution to ensure all changes persist in the repository.

## Pre-Execution

First, read the workflow documentation to ensure the complete workflow process is fresh in context:

```bash
# Load workflow documentation
cat /workspaces/agent-context-template/.claude/workflows/workflow-issue.md
```

## Usage

```bash
/workflow-issue 123
```

## Implementation

This command executes:
```bash
python /workspaces/agent-context-template/scripts/workflow_cli.py workflow-issue {issue_number}
```

This automatically enables:
- Workflow enforcement via WorkflowEnforcer
- Direct phase execution via WorkflowExecutor (no isolated agents)
- State persistence in .workflow-state-{issue_number}.json
- Phase validation before and after each step
- All changes persist in the actual repository

## What It Does

After loading the workflow documentation, directly executes each phase in the main context:

1. **Investigation** - Analyzes scope and root cause directly
2. **Planning** - Creates task templates and scratchpad files that persist
3. **Implementation** - Makes code changes directly in the repository
4. **Validation** - Runs tests and CI checks on actual code
5. **PR Creation** - Creates real PR using GitHub CLI
6. **Monitoring** - Sets up monitoring for the created PR

**Key Change**: Unlike agent delegation, all operations happen directly in the main repository context, ensuring all file changes, git operations, and GitHub actions persist.

## Options

- `--skip-phases 0,1` - Skip investigation and planning if already done
- `--type [bug|feature|hotfix]` - Optimize workflow for issue type
- `--priority [low|medium|high|critical]` - Adjust execution priority

## Example

```bash
# Full workflow for a bug
/workflow-issue 123 --type bug

# Resume from implementation (skip investigation/planning)
/workflow-issue 456 --skip-phases 0,1

# High-priority feature
/workflow-issue 789 --type feature --priority high
```

## Execution Steps

1. Read the workflow documentation from `.claude/workflows/workflow-issue.md`
2. Parse the issue number and any options provided
3. Initialize the WorkflowExecutor for direct execution
4. Execute phases directly in the main repository context
5. Track progress and handle phase transitions

## Technical Details

The command now uses `WorkflowExecutor` for direct phase execution instead of delegating to isolated agents via the Task tool. This ensures:

- All file operations create real files in the repository
- Git commands (branch, commit, push) affect the actual repository
- GitHub CLI operations (PR creation) work with real authentication
- State persistence works across all phases
- No changes are lost when phases complete
