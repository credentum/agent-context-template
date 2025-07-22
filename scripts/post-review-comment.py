#!/usr/bin/env python3
"""
GitHub Actions helper to parse claude-ci review output and format for PR comments.
Part of Issue #1063: Align GitHub Actions with Claude Local CI
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List


def parse_review_output(file_path: str) -> Dict[str, Any]:
    """Parse claude-ci review JSON output."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return {
            "status": "FAILED",
            "command": "review", 
            "errors": [{"message": f"Could not parse review output: {e}"}],
            "next_action": "Check review output format"
        }


def format_pr_comment(review_data: Dict[str, Any]) -> str:
    """Format review data as GitHub PR comment."""
    status = review_data.get("status", "UNKNOWN")
    command = review_data.get("command", "review")
    duration = review_data.get("duration", "unknown")
    next_action = review_data.get("next_action", "No action specified")
    errors = review_data.get("errors", [])
    checks = review_data.get("checks", {})
    
    # Status emoji and text
    if status == "PASSED":
        status_icon = "✅"
        status_text = "APPROVED"
        header_color = ""
    else:
        status_icon = "❌" 
        status_text = "REQUEST_CHANGES"
        header_color = ""
    
    # Build comment
    comment = f"""## {status_icon} PR Review Results

**Status:** {status_text}  
**Duration:** {duration}  
**Local Command:** `claude-ci {command}`

"""
    
    # Add detailed check results if available
    if checks:
        comment += "### Check Results\n\n"
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict):
                check_status = check_result.get("status", check_result)
            else:
                check_status = check_result
                
            check_icon = "✅" if str(check_status).upper() == "PASSED" else "❌"
            comment += f"- {check_icon} **{check_name}**: {check_status}\n"
        comment += "\n"
    
    # Add errors if any
    if errors:
        comment += "### Issues Found\n\n"
        for error in errors:
            if isinstance(error, dict):
                message = error.get("message", error.get("error", str(error)))
                file_info = ""
                if error.get("file"):
                    file_info = f" in `{error['file']}`"
                    if error.get("line"):
                        file_info += f" at line {error['line']}"
                comment += f"- {message}{file_info}\n"
            else:
                comment += f"- {error}\n"
        comment += "\n"
    
    # Add next action
    if next_action and next_action != "No action specified":
        comment += f"### Recommended Action\n\n{next_action}\n\n"
    
    # Add footer explaining the unified approach
    comment += """---

*This review uses the same `claude-ci review` command that runs locally, ensuring identical results between GitHub Actions and local development.*

**Issue #1063 Benefits:**
- ✅ **Consistent results** - Same scripts everywhere  
- 🔧 **Easy debugging** - Run `claude-ci review` locally to reproduce
- 📦 **Single source** - CI logic in scripts, not YAML
- 🎯 **Simplified workflows** - Complex review logic consolidated

*Run `claude-ci review` locally to see the same results before pushing.*"""
    
    return comment


def format_github_step_summary(review_data: Dict[str, Any]) -> str:
    """Format review data for GitHub Actions step summary."""
    status = review_data.get("status", "UNKNOWN")
    duration = review_data.get("duration", "unknown")
    checks = review_data.get("checks", {})
    errors = review_data.get("errors", [])
    
    summary = f"## 🔍 PR Review Summary\n\n"
    
    if status == "PASSED":
        summary += "✅ **Status:** APPROVED\n"
    else:
        summary += "❌ **Status:** REQUEST_CHANGES\n"
    
    summary += f"⏱️ **Duration:** {duration}\n\n"
    
    # Check breakdown
    if checks:
        summary += "### Check Results\n\n"
        for check_name, result in checks.items():
            icon = "✅" if str(result).upper() == "PASSED" else "❌"
            summary += f"{icon} {check_name}\n"
        summary += "\n"
    
    # Error count
    if errors:
        summary += f"### Issues Found: {len(errors)}\n\n"
        for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
            message = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            summary += f"{i}. {message}\n"
        
        if len(errors) > 5:
            summary += f"\n... and {len(errors) - 5} more issues\n"
        summary += "\n"
    
    summary += "**Local Command:** `claude-ci review`\n"
    summary += "*Same command works locally for consistent results.*"
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="Parse claude-ci review output for GitHub Actions")
    parser.add_argument("review_file", help="Path to claude-ci review JSON output")
    parser.add_argument("--output-format", choices=["comment", "summary", "both"], 
                       default="comment", help="Output format")
    parser.add_argument("--output-file", help="Write output to file instead of stdout")
    
    args = parser.parse_args()
    
    # Parse review output
    review_data = parse_review_output(args.review_file)
    
    # Generate output
    if args.output_format == "comment":
        output = format_pr_comment(review_data)
    elif args.output_format == "summary":
        output = format_github_step_summary(review_data)
    else:  # both
        comment = format_pr_comment(review_data)
        summary = format_github_step_summary(review_data)
        output = f"<!-- PR COMMENT -->\n{comment}\n\n<!-- STEP SUMMARY -->\n{summary}"
    
    # Write output
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(output)
    else:
        print(output)
    
    # Exit with appropriate code
    status = review_data.get("status", "UNKNOWN")
    sys.exit(0 if status == "PASSED" else 1)


if __name__ == "__main__":
    main()