#!/usr/bin/env python3
"""
Script to update coverage baseline references in CLAUDE.md from .coverage-config.json
"""
import json
import re
from pathlib import Path


def update_claude_md():
    """Update CLAUDE.md with current coverage baseline from config"""

    # Load coverage config
    config_file = Path(".coverage-config.json")
    if not config_file.exists():
        print("❌ .coverage-config.json not found")
        return False

    with open(config_file) as f:
        config = json.load(f)

    baseline = config["baseline"]
    target = config["target"]
    validator_target = config["validator_target"]

    # Update CLAUDE.md
    claude_md = Path("CLAUDE.md")
    if not claude_md.exists():
        print("❌ CLAUDE.md not found")
        return False

    content = claude_md.read_text()

    # Update the coverage line
    pattern = r"- Coverage: [\d.]+% \(Current baseline\)"
    replacement = f"- Coverage: {baseline}% (Current baseline)"

    new_content = re.sub(pattern, replacement, content)

    # Update target references if they exist
    target_pattern = r"Target: [\d.]+% for all modules, [\d.]+% for validators"
    target_replacement = f"Target: {target}% for all modules, {validator_target}% for validators"

    new_content = re.sub(target_pattern, target_replacement, new_content)

    if content != new_content:
        claude_md.write_text(new_content)
        print(
            f"✅ Updated CLAUDE.md with baseline: {baseline}%, "
            f"target: {target}%, validator target: {validator_target}%"
        )
        return True
    else:
        print(f"ℹ️ CLAUDE.md already up to date with baseline: {baseline}%")
        return False


if __name__ == "__main__":
    update_claude_md()
