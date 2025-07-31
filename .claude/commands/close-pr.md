# Close PR Command

Cleanup workflow after PR work: clears context, switches to main, pulls latest, cleans up local branches, and exits.

## Usage

```bash
/close-pr
```

## Implementation

This command executes a series of cleanup operations:

1. Clear the current context using `/clear`
2. Switch to the main branch
3. Pull latest changes from remote main
4. Clean up local branches (remove merged branches)
5. Exit the Claude session

## What It Does

Performs a complete cleanup workflow to reset your environment after PR work:

```bash
# 1. Clear context
/clear

# 2. Switch to main branch
git checkout main

# 3. Pull latest changes
git pull origin main

# 4. Clean up merged branches
git branch --merged | grep -v "\*\|main" | xargs -n 1 git branch -d

# 5. Exit session
exit
```

## Example

```bash
# After finishing PR work
/close-pr
```

## Notes

- Ensures you're back on an updated main branch
- Removes only merged branches (safe cleanup)
- Clears Claude context to start fresh next time
- Automatically exits after cleanup
