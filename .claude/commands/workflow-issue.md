# Workflow Issue Command

Execute the complete issue-to-PR workflow with automatic phase delegation to specialized agents.

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

## What It Does

After loading the workflow documentation, automatically coordinates the entire issue resolution process:

1. **Investigation** (issue-investigator agent) - Analyzes scope and root cause
2. **Planning** (task-planner agent) - Creates detailed implementation plan
3. **Implementation** (main Claude) - Executes the plan
4. **Validation** (test-runner agent) - Ensures quality with tests
5. **PR Creation** (pr-manager agent) - Creates and configures PR
6. **Monitoring** (pr-manager agent) - Tracks PR to completion

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
3. Initialize the workflow coordinator agent
4. Execute phases based on the workflow documentation
5. Track progress and handle phase transitions

The workflow coordinator will delegate each phase to the appropriate specialist agent and manage the transitions between phases.
