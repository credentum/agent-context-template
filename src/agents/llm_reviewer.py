#!/usr/bin/env python3
"""
LLM-based ARC-Reviewer using Claude API.

Implements the same review logic as the GitHub Actions workflow
claude-code-review.yml but using the Anthropic Claude API for local execution.
"""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore


class LLMReviewer:
    """
    LLM-based ARC Reviewer using Claude API.

    Implements the same review logic as GitHub Actions workflow but locally.
    """

    def __init__(self, api_key: Optional[str] = None, verbose: bool = False, timeout: int = 120):
        """Initialize the LLM Reviewer.

        Args:
            api_key: Anthropic API key (if None, tries environment variable)
            verbose: Enable verbose output
            timeout: Maximum seconds for command execution
        """
        if anthropic is None:
            raise ImportError(
                "anthropic package is required for LLMReviewer. "
                "Install with: pip install anthropic>=0.8.0"
            )

        self.api_key = api_key or os.getenv("CLAUDE_CODE_OAUTH_TOKEN")
        if not self.api_key:
            raise ValueError(
                "CLAUDE_CODE_OAUTH_TOKEN must be provided either as parameter "
                "or environment variable"
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.verbose = verbose
        self.timeout = timeout
        self.repo_root = Path(__file__).parent.parent.parent

    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        if cwd is None:
            cwd = self.repo_root

        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=self.timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {self.timeout} seconds"
        except Exception as e:
            return 1, "", str(e)

    def _tool_bash(self, command: str) -> str:
        """Execute bash command (mimics GitHub Actions Bash tool)."""
        if self.verbose:
            print(f"🔧 Executing: {command}")

        exit_code, stdout, stderr = self._run_command(command.split(), self.repo_root)

        if exit_code == 0:
            return stdout
        else:
            return f"Command failed (exit {exit_code}): {stderr}"

    def _tool_read(self, file_path: str) -> str:
        """Read file contents (mimics GitHub Actions Read tool)."""
        try:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                return f"File not found: {file_path}"

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Format with line numbers like the actual Read tool
            lines = content.split("\n")
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                numbered_lines.append(f"{i:6}→{line}")

            return "\n".join(numbered_lines)

        except Exception as e:
            return f"Error reading {file_path}: {str(e)}"

    def _tool_grep(self, pattern: str, file_pattern: str = "**/*") -> str:
        """Search for pattern in files (mimics GitHub Actions Grep tool)."""
        cmd = ["grep", "-r", "-n", pattern, "."]
        if file_pattern != "**/*":
            # Simple glob to file extension filtering
            if file_pattern.endswith("*.py"):
                cmd.extend(["--include=*.py"])
            elif file_pattern.endswith("*.yaml"):
                cmd.extend(["--include=*.yaml", "--include=*.yml"])

        exit_code, stdout, stderr = self._run_command(cmd, self.repo_root)

        if exit_code == 0:
            return stdout
        elif exit_code == 1:  # No matches found
            return "No matches found"
        else:
            return f"Grep failed: {stderr}"

    def _tool_glob(self, pattern: str) -> str:
        """Find files matching glob pattern (mimics GitHub Actions Glob tool)."""
        cmd = ["find", ".", "-name", pattern, "-type", "f"]
        exit_code, stdout, stderr = self._run_command(cmd, self.repo_root)

        if exit_code == 0:
            return stdout
        else:
            return f"Find failed: {stderr}"

    def _get_prompt_template(self) -> str:
        """Get the exact prompt template from GitHub Actions workflow."""
        return """You are ARC-Reviewer, a senior staff engineer reviewing \
pull-requests on the agent-context-template (MCP-based context platform).

CRITICAL: Output ONLY valid YAML. No markdown, no explanations, \
no code blocks. Start directly with the YAML schema.
FORMATTING: Ensure consistent YAML formatting for both initial reviews \
and subsequent edits.
COMMENT_FORMAT: Use identical structure and indentation for all review \
iterations.

🔍 REVIEW SCOPE: You must review the ENTIRE cumulative PR state, not just recent changes.
Use 'git diff --name-only origin/main...HEAD' to see ALL changed files in the PR.
Read the complete current state of ALL modified files, not just the latest diff.
Consider all issues that may exist across the entire changeset, including:
- Issues identified in previous reviews that may still exist
- New issues introduced by any changes in the PR
- Cumulative effects of all changes together

Review criteria (any failure = REQUEST_CHANGES):
- Test Coverage: validators/* ≥ 90%, overall ≥ 78.0%
- MCP Compatibility: Tool contracts updated, valid JSON schema
- Context Integrity: All YAML has schema_version, context/ structure intact
- Code Quality: Python typed, docstrings, pre-commit passes
- Security: Dockerfiles pinned digests, no secrets, CVE-free deps

For blocking issues, be specific about:
- What is wrong (description)
- Where it's located (file and line)
- What category it falls under
- How to fix it (actionable guidance)

Output this exact YAML structure (replace bracketed values with actuals).
IMPORTANT: Use identical formatting, indentation, and structure for all reviews:

schema_version: "1.0"
pr_number: [ACTUAL_PR_NUMBER]
timestamp: "[CURRENT_ISO_TIMESTAMP]"
reviewer: "ARC-Reviewer"
verdict: "APPROVE"
summary: "Brief review summary"
coverage:
  current_pct: [ACTUAL_PERCENTAGE]
  status: "PASS"
  meets_baseline: true
issues:
  blocking:
    - description: "Specific actionable description of what must be fixed"
      file: "relative/path/to/file.py"
      line: 42
      category: "test_coverage"
      fix_guidance: "Add unit tests for the new function"
  warnings:
    - description: "High-priority improvement needed"
      file: "path/to/file.py"
      line: 15
      category: "code_quality"
      fix_guidance: "Add type hints to this function"
  nits:
    - description: "Style or minor improvement"
      file: "path/to/file.py"
      line: 8
      category: "style"
      fix_guidance: "Use more descriptive variable name"
automated_issues:
  - title: "Follow-up issue title"
    description: "Detailed description for GitHub issue"
    labels: ["enhancement", "test"]
    phase: "4.1"
    priority: "high"
    category: "test_coverage\""""

    def review_pr(
        self, pr_number: Optional[int] = None, base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Perform LLM-based PR review using Claude API.

        Args:
            pr_number: PR number (optional, used for metadata)
            base_branch: Base branch to compare against

        Returns:
            Dictionary with review results in same format as ARCReviewer
        """
        if self.verbose:
            print("🤖 Starting LLM-based ARC-Reviewer analysis...")

        try:
            # Get the diff and changed files context
            diff_cmd = f"git diff --name-only origin/{base_branch}...HEAD"
            exit_code, changed_files_output, stderr = self._run_command(diff_cmd.split())

            if exit_code != 0:
                if self.verbose:
                    print(f"Warning: Could not get changed files: {stderr}")
                changed_files_output = ""

            # Get the full diff for context
            full_diff_cmd = f"git diff origin/{base_branch}...HEAD"
            exit_code, full_diff, stderr = self._run_command(full_diff_cmd.split())

            if exit_code != 0:
                if self.verbose:
                    print(f"Warning: Could not get full diff: {stderr}")
                full_diff = ""

            # Create the context message for Claude
            context_message = f"""Please review this PR against the criteria specified.

Changed files:
{changed_files_output}

Full diff:
{full_diff}

PR number: {pr_number or 'local'}
Base branch: {base_branch}
Timestamp: {datetime.now(timezone.utc).isoformat()}

You have access to these tools:
- Bash(command): Execute bash commands
- Read(file_path): Read file contents
- Grep(pattern, file_pattern): Search for patterns
- Glob(pattern): Find files matching pattern

Please review the entire PR state and provide your assessment in the required YAML format."""

            # Call Claude API with tool use capability
            if self.verbose:
                print("🔄 Calling Claude API for review...")

            # Define available tools for Claude
            tools: list[dict[str, Any]] = [
                {
                    "name": "bash",
                    "description": "Execute a bash command",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The bash command to execute",
                            }
                        },
                        "required": ["command"],
                    },
                },
                {
                    "name": "read",
                    "description": "Read the contents of a file",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read",
                            }
                        },
                        "required": ["file_path"],
                    },
                },
                {
                    "name": "grep",
                    "description": "Search for a pattern in files",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Pattern to search for"},
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to search in",
                                "default": "**/*",
                            },
                        },
                        "required": ["pattern"],
                    },
                },
                {
                    "name": "glob",
                    "description": "Find files matching a pattern",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Glob pattern to match"}
                        },
                        "required": ["pattern"],
                    },
                },
            ]

            # Start conversation with Claude
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                tools=tools,  # type: ignore
                messages=[
                    {
                        "role": "user",
                        "content": self._get_prompt_template() + "\n\n" + context_message,
                    }
                ],
            )

            # Handle tool use if Claude requests it
            conversation = [
                {"role": "user", "content": self._get_prompt_template() + "\n\n" + context_message},
                {"role": "assistant", "content": message.content},
            ]

            # Process tool use requests
            while any(block.type == "tool_use" for block in message.content):
                tool_results = []

                for block in message.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        if self.verbose:
                            print(f"🔧 Claude requested tool: {tool_name} with {tool_input}")

                        # Execute the requested tool
                        if tool_name == "bash":
                            result = self._tool_bash(tool_input["command"])  # type: ignore
                        elif tool_name == "read":
                            result = self._tool_read(tool_input["file_path"])  # type: ignore
                        elif tool_name == "grep":
                            file_pattern = tool_input.get("file_pattern", "**/*")  # type: ignore
                            result = self._tool_grep(tool_input["pattern"], file_pattern)  # type: ignore
                        elif tool_name == "glob":
                            result = self._tool_glob(tool_input["pattern"])  # type: ignore
                        else:
                            result = f"Unknown tool: {tool_name}"

                        tool_results.append({"tool_use_id": block.id, "content": result})

                # Send tool results back to Claude
                conversation.append({"role": "user", "content": tool_results})

                # Get Claude's next response
                message = self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    tools=tools,  # type: ignore
                    messages=conversation,  # type: ignore
                )

                conversation.append({"role": "assistant", "content": message.content})

            # Extract final response
            final_response = ""
            for block in message.content:
                if block.type == "text":
                    final_response += block.text

            if self.verbose:
                print(f"📋 Claude response length: {len(final_response)} characters")

            # Parse the YAML response
            try:
                review_data = yaml.safe_load(final_response)

                if not isinstance(review_data, dict):
                    raise ValueError("Response is not a valid YAML dictionary")

                # Ensure required fields
                review_data.setdefault("schema_version", "1.0")
                review_data.setdefault("pr_number", pr_number or 0)
                review_data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                review_data.setdefault("reviewer", "ARC-Reviewer (LLM)")

                if self.verbose:
                    verdict = review_data.get("verdict", "UNKNOWN")
                    print(f"✅ Successfully parsed review with verdict: {verdict}")

                return review_data

            except yaml.YAMLError as e:
                if self.verbose:
                    print(f"❌ Failed to parse YAML response: {e}")
                    print(f"Raw response: {final_response[:500]}...")

                # Return fallback response
                return {
                    "schema_version": "1.0",
                    "pr_number": pr_number or 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reviewer": "ARC-Reviewer (LLM)",
                    "verdict": "REQUEST_CHANGES",
                    "summary": "LLM review failed - YAML parsing error",
                    "coverage": {"current_pct": 0.0, "status": "UNKNOWN", "meets_baseline": False},
                    "issues": {
                        "blocking": [
                            {
                                "description": f"LLM response parsing failed: {str(e)}",
                                "file": "llm_response",
                                "line": 0,
                                "category": "llm_error",
                                "fix_guidance": "Check LLM response format and API connection",
                            }
                        ],
                        "warnings": [],
                        "nits": [],
                    },
                    "automated_issues": [],
                }

        except Exception as e:
            if self.verbose:
                print(f"❌ LLM review failed: {str(e)}")

            # Return error response
            return {
                "schema_version": "1.0",
                "pr_number": pr_number or 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reviewer": "ARC-Reviewer (LLM)",
                "verdict": "REQUEST_CHANGES",
                "summary": f"LLM review failed: {str(e)}",
                "coverage": {"current_pct": 0.0, "status": "ERROR", "meets_baseline": False},
                "issues": {
                    "blocking": [
                        {
                            "description": f"LLM API error: {str(e)}",
                            "file": "llm_api",
                            "line": 0,
                            "category": "llm_error",
                            "fix_guidance": "Check API key and network connection",
                        }
                    ],
                    "warnings": [],
                    "nits": [],
                },
                "automated_issues": [],
            }

    def format_yaml_output(self, review_data: Dict[str, Any]) -> str:
        """Format review results as YAML string matching workflow output."""
        return yaml.dump(review_data, default_flow_style=False, sort_keys=False)
