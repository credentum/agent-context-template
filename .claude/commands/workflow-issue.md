# Workflow Issue Command

Execute the complete issue-to-PR workflow with direct phase execution to ensure all changes persist in the repository.

## Important: Timeout Considerations

Due to Claude's 2-minute command timeout limit, use the phase-based runner for reliable execution:

```bash
# Recommended: Use phase-based runner (timeout-safe)
python /workspaces/agent-context-template/scripts/workflow_phase_runner.py {issue_number} --hybrid

# Alternative: Direct execution (may timeout)
/workflow-issue {issue_number} --hybrid
```

## Pre-Execution

### Step 1: Set up Isolated Workspace (Git Worktree)

Create a git worktree for isolated issue development:

```bash
# Set up isolated workspace for this issue
echo "🔧 Setting up isolated workspace..."

# Ensure we're in the main repository root
cd /workspaces/agent-context-template

# Create worktree directory if not exists
mkdir -p /workspaces/agent-context-template/worktree

# Create git worktree for this issue with feature branch
git worktree add /workspaces/agent-context-template/worktree/issue-{issue_number} -b feature/issue-{issue_number}

# Change to worktree directory
cd /workspaces/agent-context-template/worktree/issue-{issue_number}

# Verify we're in the right place
echo "✅ Working in: $(pwd)"
echo "✅ Branch: $(git branch --show-current)"
```

### Step 2: Load Workflow Documentation

Read the workflow documentation to ensure the complete workflow process is fresh in context:

```bash
# Load workflow documentation (from worktree context)
cat /workspaces/agent-context-template/.claude/workflows/workflow-issue.md
```

## Usage

```bash
/workflow-issue 123

# With hybrid mode for enhanced specialist analysis
/workflow-issue 123 --hybrid
```

## Implementation

This command executes from the isolated worktree directory:
```bash
# Execute from worktree (after worktree setup)
cd /workspaces/agent-context-template/worktree/issue-{issue_number}
python /workspaces/agent-context-template/scripts/workflow_cli.py workflow-issue {issue_number}
```

This automatically enables:
- **Isolated workspace** in `/workspaces/agent-context-template/worktree/issue-{issue_number}/`
- **Automatic feature branch** creation (`feature/issue-{issue_number}`)
- Workflow enforcement via WorkflowEnforcer
- Direct phase execution via WorkflowExecutor (no isolated agents)
- State persistence in .workflow-state-{issue_number}.json
- Phase validation before and after each step
- All changes persist in the worktree repository
- **NEW**: Hybrid mode option with specialist sub-agents (--hybrid)

## What It Does

After setting up the isolated worktree and loading workflow documentation, directly executes each phase:

0. **Worktree Setup** - Creates isolated workspace in `/workspaces/agent-context-template/worktree/issue-{issue_number}/`
1. **Investigation** - Analyzes scope and root cause directly in worktree
2. **Planning** - Creates task templates and scratchpad files that persist in worktree
3. **Implementation** - Makes code changes directly in the isolated repository (branch already created)
4. **Validation** - Runs tests and CI checks on actual code in worktree
5. **PR Creation** - Creates real PR using GitHub CLI from worktree branch
6. **Monitoring** - Sets up monitoring for the created PR

**Key Benefits**:
- **Isolation**: Each issue gets its own workspace, preventing interference
- **Concurrent Work**: Multiple issues can be developed simultaneously
- **Clean Main**: Main working directory stays untouched
- **Direct Execution**: All operations happen directly in the worktree, ensuring persistence

## Options

- `--skip-phases 0,1` - Skip investigation and planning if already done
- `--type [bug|feature|hotfix]` - Optimize workflow for issue type
- `--priority [low|medium|high|critical]` - Adjust execution priority
- `--hybrid` - **NEW**: Enable hybrid mode with specialist sub-agents for enhanced analysis

## Example

```bash
# Full workflow for a bug
/workflow-issue 123 --type bug

# Resume from implementation (skip investigation/planning)
/workflow-issue 456 --skip-phases 0,1

# High-priority feature
/workflow-issue 789 --type feature --priority high

# Complex issue with hybrid mode for specialist analysis
/workflow-issue 890 --hybrid --type feature

# Combine hybrid mode with other options
/workflow-issue 901 --hybrid --priority high --skip-phases 0
```

## Execution Steps

1. **Worktree Setup**: Create isolated workspace in `/workspaces/agent-context-template/worktree/issue-{issue_number}/`
2. **Branch Creation**: Automatically create feature branch `feature/issue-{issue_number}`
3. **Context Switch**: Change to worktree directory for all subsequent operations
4. **Documentation Load**: Read workflow documentation from `.claude/workflows/workflow-issue.md`
5. **Parse Options**: Parse the issue number and any options provided
6. **Initialize Executor**: Initialize the WorkflowExecutor for direct execution in worktree
7. **Execute Phases**: Execute phases directly in the isolated worktree context
8. **Track Progress**: Track progress and handle phase transitions with state persistence

## Technical Details

The command uses `WorkflowExecutor` for direct phase execution in an isolated git worktree. This ensures:

- **Workspace Isolation**: Each issue works in `/workspaces/agent-context-template/worktree/issue-{issue_number}/`
- **Automatic Branching**: Feature branch `feature/issue-{issue_number}` created with worktree
- **Real File Operations**: All file operations create real files in the isolated repository
- **Git Operations**: Git commands (commit, push) affect the worktree repository and branch
- **GitHub Integration**: GitHub CLI operations (PR creation) work with real authentication from worktree
- **State Persistence**: State persists across all phases within the worktree
- **No Interference**: Multiple concurrent workflows don't conflict
- **Easy Cleanup**: `git worktree remove` cleans up completely when done

## Hybrid Mode

When using the `--hybrid` flag, the command uses `HybridWorkflowExecutor` which enhances the base workflow with specialist sub-agents:

### What Hybrid Mode Does
- Maintains all direct execution benefits of WorkflowExecutor
- Adds specialist consultants for complex analysis tasks
- Specialists provide insights without handling persistence
- Gracefully falls back to basic mode if specialists fail

### Specialist Integration Points
- **Investigation Phase**: Uses `issue-investigator` for deep root cause analysis
- **Planning Phase**: Uses `general-purpose` for codebase research and patterns
- **Validation Phase**: Uses `test-runner` and `security-analyzer` in parallel

### When to Use Hybrid Mode
- Complex architectural issues requiring deep analysis
- Large codebases with many affected files (>10)
- Critical changes needing enhanced validation
- Issues marked as "high complexity" or "investigation needed"

### Example Output with Hybrid Mode
```
🔍 Executing investigation phase (hybrid mode)...
  🤖 Consulting issue-investigator specialist...
  ✅ Specialist provided additional insights
```

## Worktree Management

### Automatic Setup
The workflow automatically creates and manages git worktrees:

```bash
# This happens automatically when you run /workflow-issue 123
/workspaces/agent-context-template/worktree/issue-123/  # ← Isolated workspace
  ├── .git           # ← Points to main repo
  ├── src/           # ← Full copy of source code
  ├── scripts/       # ← All scripts available
  └── ...            # ← Complete repository structure
```

### Manual Cleanup
After PR is merged, clean up the worktree:

```bash
# Remove completed worktree (run from main directory)
cd /workspaces/agent-context-template
git worktree remove worktree/issue-123

# List all worktrees
git worktree list

# Remove all merged worktrees (future automation)
git worktree prune
```

### Concurrent Development
Work on multiple issues simultaneously:

```bash
# Terminal 1: Working on issue 123
/workflow-issue 123 --type bug

# Terminal 2: Working on issue 456 (different workspace)
/workflow-issue 456 --type feature

# Terminal 3: Main directory stays clean for other work
cd /workspaces/agent-context-template  # ← Always on main branch
```

### Troubleshooting Worktrees

**If worktree creation fails:**
```bash
# Check existing worktrees
git worktree list

# Remove stale worktree if needed
git worktree remove worktree/issue-123 --force

# Retry workflow
/workflow-issue 123
```

**If branch already exists:**
```bash
# The workflow will handle existing branches gracefully
# Or manually clean up if needed
git branch -D feature/issue-123  # Delete local branch
git push origin --delete feature/issue-123  # Delete remote branch
```
