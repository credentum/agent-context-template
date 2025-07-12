# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Context

This is a **GitHub Actions template repository** that provides workflow templates for integrating Claude AI into GitHub workflows using the `anthropics/claude-code-action@beta` action.

## 1 ⚠️ Security & Secrets (first things first)
* **Never hard‑code API keys or tokens.**  
  
  **For OAuth authentication (recommended):**
  Add `CLAUDE_CODE_OAUTH_TOKEN` in GitHub Secrets:
  ```yaml
  claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
  ```
  
  **For API key authentication:**
  Add `ANTHROPIC_API_KEY` in GitHub Secrets:
  ```yaml
  anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
  ```

Grant the minimal permissions: your workflow needs, e.g.

permissions:
  contents: read          # read repo
  pull-requests: write    # create / update PRs
To run unattended you may append --dangerously-skip-permissions.
Only do this inside a throw‑away container or GitHub runner; it bypasses every safety prompt.

2 🚀 Quick Start
Install CLI (once per machine):

npm install -g @anthropic-ai/claude-code
Bootstrap in repo root:

claude          # starts interactive session
/init           # generates initial CLAUDE.md (this file)
Tag @claude in any issue / PR to summon the GitHub Action.

3 🛠️ CLI Cheat‑Sheet (keep nearby)
claude -c or --continue – reopen last session

/clear – wipe context; use between tasks

/compact – summarise convo to free tokens

/review – AI code‑review current diff or PR

/model – switch between models (e.g., claude-opus-4-20250514, claude-sonnet-4-20250514)

/help – list all slash commands

Headless mode: claude -p "<prompt>" --output-format stream-json

Add tools: claude mcp add playwright npx @playwright/mcp@latest

4 📋 Coding & Review Guidelines

Language style: follow Prettier‑default for JS/TS, Black for Python.
Tests: must accompany any new logic; ask /review to verify coverage.
Commits: imperative mood, <scope>: <verb> … (Conventional Commits).
Branching: feat/*, fix/*, chore/*; squash‑merge preferred.

5 🔄 Recommended Workflows
When	Ask Claude to…
Small fix	read files → plan → patch → /review → commit
New feature	TDD: write failing tests → commit → implement until green
Design spike	ultrathink prompt to draft high‑level design doc
Large refactor	generate checklist file → iteratively tick items

Use /clear between distinct threads to avoid context bleed.

6 ▶️ GitHub Actions Overview

**.github/workflows/claude.yml** — Interactive assistant that triggers on:
- Issue comments containing `@claude`
- Pull request review comments containing `@claude`  
- Issues opened/assigned with `@claude` in title/body
- Pull request reviews containing `@claude`

**.github/workflows/claude-code-review.yml** — Automated code review on:
- Pull request opened/synchronized events
- No `@claude` mention required
- Uses `direct_prompt` for automated review instructions

**Configuration options include:**
```yaml
model: "claude-opus-4-20250514"  # or claude-sonnet-4-20250514
max_turns: 3                      # limit conversation turns
timeout_minutes: 10               # job timeout
allowed_tools: "Bash(npm test),Bash(npm run lint)"
direct_prompt: |                  # for automated reviews
  Review for code quality and bugs
use_sticky_comment: true          # reuse same PR comment
assignee_trigger: "username"     # trigger on assignment
label_trigger: "needs-claude"    # trigger on label
```

7 💰 Tokens & Cost Control
Run npx ccusage@latest locally to inspect monthly token burn.
Keep prompts tight; prefer bullet lists to prose.
Use /compact every ~100 lines of dialogue.
In Actions set max_turns: 3 unless the task truly needs more.

8 🧩 Extending Claude
Custom slash commands: place Markdown files in .claude/commands/; they become /project:<name>.
Multi‑Claude pattern: open extra terminals / worktrees, dedicate one Claude instance to dev, another to review, a third to tests.
Headless pipelines: wire claude -p into CI scripts for migrations or lint fixes.

9 📚 Further Reading
Anthropic "Best practices for agentic coding" (Apr 2025)
Claude Code GitHub Actions docs & examples
Model Context Protocol (MCP) specs

# 🚨 CRITICAL: Git Workflow Rules

**NEVER push directly to main branch!** Always follow this workflow:

1. Start from updated main:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create a feature branch:
   ```bash
   git checkout -b fix/description
   # or
   git checkout -b feature/description
   ```

3. Make changes and commit:
   ```bash
   git add -A
   git commit -m "type: description"
   ```

4. Push to feature branch:
   ```bash
   git push -u origin fix/description
   ```

5. Create PR:
   ```bash
   gh pr create --title "type: description" --body "..."
   ```

**IMPORTANT**: 
- NEVER use `git push origin main`
- ALWAYS create a PR for code review
- Include test results in PR descriptions
- Wait for CI checks to pass before merging