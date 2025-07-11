# CLAUDE.md


## 1 ⚠️ Security & Secrets (first things first)
* **Never hard‑code API keys.**  
  Add `ANTHROPIC_API_KEY` (or Bedrock / Vertex creds) in **GitHub Secrets** and reference it in workflows:  

  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

Grant the minimal permissions: your workflow needs, e.g.

permissions:
  contents: read          # read repo
  pull-requests: write    # create / update PRs
To run unattended you may append --dangerously-skip-permissions.
Only do this inside a throw‑away container or GitHub runner; it bypasses every safety prompt.

2 🚀 Quick Start
Install CLI (once per machine):

npm install -g @anthropic-ai/claude-code
Bootstrap in repo root:

claude          # starts interactive session
/init           # generates initial CLAUDE.md (this file)
Tag @claude in any issue / PR to summon the GitHub Action.

3 🛠️ CLI Cheat‑Sheet (keep nearby)
claude -c or --continue – reopen last session

/clear – wipe context; use between tasks

/compact – summarise convo to free tokens

/review – AI code‑review current diff or PR

/model – switch (opus | sonnet | haiku) on the fly

/help – list all slash commands

Headless mode: claude -p "<prompt>" --output-format stream-json

Add tools: claude mcp add playwright npx @playwright/mcp@latest

4 📋 Coding & Review Guidelines

Language style: follow Prettier‑default for JS/TS, Black for Python.
Tests: must accompany any new logic; ask /review to verify coverage.
Commits: imperative mood, <scope>: <verb> … (Conventional Commits).
Branching: feat/*, fix/*, chore/*; squash‑merge preferred.

5 🔄 Recommended Workflows
When	Ask Claude to…
Small fix	read files → plan → patch → /review → commit
New feature	TDD: write failing tests → commit → implement until green
Design spike	ultrathink prompt to draft high‑level design doc
Large refactor	generate checklist file → iteratively tick items

Use /clear between distinct threads to avoid context bleed.

6 ▶️ GitHub Actions Overview
.github/workflows/claude.yml — interactive assistant; triggers on @claude.
.github/workflows/claude-code-review.yml — auto review on pull_request open/sync.
Configure via inputs:: model, max_turns, timeout_minutes, allowed_tools.
Control costs with runner concurrency: and low max_turns.

7 💰 Tokens & Cost Control
Run npx ccusage@latest locally to inspect monthly token burn.
Keep prompts tight; prefer bullet lists to prose.
Use /compact every ~100 lines of dialogue.
In Actions set max_turns: 3 unless the task truly needs more.

8 🧩 Extending Claude
Custom slash commands: place Markdown files in .claude/commands/; they become /project:<name>.
Multi‑Claude pattern: open extra terminals / worktrees, dedicate one Claude instance to dev, another to review, a third to tests.
Headless pipelines: wire claude -p into CI scripts for migrations or lint fixes.

9 📚 Further Reading
Anthropic “Best practices for agentic coding” (Apr 2025)
Claude Code GitHub Actions docs & examples
Model Context Protocol (MCP) specs