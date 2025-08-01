#!/bin/bash
# Post-create command for codespace
# Automatically sets up the environment for autonomous PR creation

echo "🔧 Setting up autonomous PR environment..."

# Fix authentication issues
if [[ -n "$GITHUB_TOKEN" && "$GITHUB_TOKEN" == ghu_* ]]; then
    echo "⚠️  Detected codespace token - configuring for autonomous PR creation"

    # Don't unset here, but add warning to profile
    echo 'export AUTONOMOUS_PR_WARNING="Warning: Use unset GITHUB_TOKEN before creating PRs"' >> ~/.bashrc
fi

# Add helpful aliases
echo 'alias create-pr="/workspaces/agent-context-template/scripts/create-autonomous-pr.sh"' >> ~/.bashrc
echo 'alias fix-pr-auth="unset GITHUB_TOKEN && echo \"✅ GitHub token cleared for autonomous PR creation\""' >> ~/.bashrc

# Create helpful reminder
cat << 'EOF' >> ~/.bashrc

# Autonomous PR Creation Helper
autonomous-pr-help() {
    echo "🚀 Autonomous PR Creation Commands:"
    echo ""
    echo "1. Fix authentication: fix-pr-auth"
    echo "2. Create PR: create-pr --repo OWNER/REPO --title 'Title' --body 'Description'"
    echo ""
    echo "Example:"
    echo "  create-pr --repo credentum/context-store --title 'feat: New feature' --body 'Added functionality'"
    echo ""
    echo "Troubleshooting:"
    echo "  - If authentication fails, check PERSONAL_ACCESS_TOKEN secret"
    echo "  - Token scopes needed: repo, workflow, read:org"
    echo "  - Generate at: https://github.com/settings/tokens"
}

EOF

echo "✅ Autonomous PR environment configured!"
echo "Run 'autonomous-pr-help' for usage instructions"
