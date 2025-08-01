# Create PR Command

Create pull requests autonomously from codespaces with automatic issue resolution.

## Usage

```bash
/create-pr --repo OWNER/REPO --title "PR Title" --body "PR Description" [options]
```

## Implementation

This command uses our battle-tested script that resolves all known authentication and branch issues:

```bash
# Execute the autonomous PR creation script
./scripts/create-autonomous-pr.sh "$@"
```

## Examples

```bash
# Basic PR creation
/create-pr --repo credentum/context-store --title "feat: Add new schemas" --body "Comprehensive schema collection for AI workflows"

# With custom branch name
/create-pr --repo credentum/context-store --title "fix: Bug fix" --body "Resolves authentication issues" --branch fix/auth-bug

# With custom base branch
/create-pr --repo credentum/context-store --title "feat: New feature" --body "Feature description" --base develop
```

## Options

- `--repo`: Target repository (required) - format: `OWNER/REPO`
- `--title`: PR title (required)
- `--body`: PR description (required)
- `--branch`: Branch name (optional, auto-generated if not provided)
- `--base`: Base branch (optional, defaults to `main`)

## What It Does

1. **Fixes Authentication**: Automatically handles token override issues
2. **Creates Proper Branch**: Creates branch from correct base with proper history
3. **Commits Changes**: Commits any staged changes with proper formatting
4. **Pushes Branch**: Pushes to remote repository
5. **Creates PR**: Uses REST API to create pull request (bypasses GraphQL issues)
6. **Returns URL**: Provides direct link to created PR

## Prerequisites

1. **Personal Access Token**: Set as `PERSONAL_ACCESS_TOKEN` codespace secret
2. **Token Scopes**: `repo`, `workflow`, `read:org`, `write:discussion`
3. **Repository Access**: Token user must have write access to target repository
4. **Changes Ready**: Make your changes and stage them (`git add .`) before running

## Error Handling

The script provides detailed error messages and solutions for common issues:
- Invalid or expired tokens
- Missing repository access
- Branch creation failures
- Network connectivity issues

## Troubleshooting

If the command fails, see the comprehensive troubleshooting guide:
`.claude/troubleshooting/autonomous-pr-creation.md`

## Quick Fixes

```bash
# Fix authentication issues
unset GITHUB_TOKEN

# Test your setup
curl -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user

# Get help
autonomous-pr-help
```
