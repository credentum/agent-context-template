#!/usr/bin/env python3
"""
Sprint Issue Linker - Creates GitHub issues from sprint tasks

This script helps create GitHub issues that are properly linked
to sprint tasks for automated tracking.
"""

import os
import sys
import yaml
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import click


class SprintIssueLinker:
    """Links sprint tasks with GitHub issues"""
    
    def __init__(self, sprint_id: Optional[str] = None, dry_run: bool = False, verbose: bool = False):
        self.sprint_id = sprint_id
        self.dry_run = dry_run
        self.verbose = verbose
        self.context_dir = Path("context")
        self.sprints_dir = self.context_dir / "sprints"
        
    def _get_sprint_file(self) -> Optional[Path]:
        """Get the sprint file to work with"""
        if self.sprint_id:
            sprint_file = self.sprints_dir / f"{self.sprint_id}.yaml"
            if sprint_file.exists():
                return sprint_file
        else:
            # Find active sprint
            for sprint_file in sorted(self.sprints_dir.glob("sprint-*.yaml"), reverse=True):
                try:
                    with open(sprint_file, 'r') as f:
                        data = yaml.safe_load(f)
                    if data.get('status') in ['planning', 'in_progress']:
                        return sprint_file
                except Exception:
                    continue
        return None
    
    def _get_existing_issues(self, sprint_label: str) -> List[Dict[str, Any]]:
        """Get existing issues with the sprint label"""
        try:
            cmd = ["gh", "issue", "list", "--label", sprint_label, "--json", "number,title,state,body", "--limit", "100"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except Exception as e:
            if self.verbose:
                click.echo(f"Error fetching issues: {e}")
            return []
    
    def _create_issue(self, title: str, body: str, labels: List[str]) -> Optional[int]:
        """Create a GitHub issue"""
        if self.dry_run:
            click.echo(f"[DRY RUN] Would create issue: {title}")
            if self.verbose:
                click.echo(f"  Labels: {', '.join(labels)}")
                click.echo(f"  Body preview: {body[:200]}...")
            return None
        
        try:
            cmd = ["gh", "issue", "create", "--title", title, "--body", body]
            for label in labels:
                cmd.extend(["--label", label])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Extract issue number from output
            if result.stdout:
                # Output typically includes the issue URL
                parts = result.stdout.strip().split('/')
                issue_number = int(parts[-1])
                click.echo(f"✓ Created issue #{issue_number}: {title}")
                return issue_number
        except Exception as e:
            click.echo(f"✗ Failed to create issue: {e}")
        
        return None
    
    def create_issues_from_sprint(self) -> int:
        """Create GitHub issues from sprint tasks"""
        sprint_file = self._get_sprint_file()
        if not sprint_file:
            click.echo("No active sprint found")
            return 0
        
        # Load sprint data
        try:
            with open(sprint_file, 'r') as f:
                sprint_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return 0
        
        sprint_number = sprint_data.get('sprint_number', 1)
        sprint_label = f"sprint-{sprint_number}"
        sprint_title = sprint_data.get('title', f'Sprint {sprint_number}')
        
        click.echo(f"Processing {sprint_title} from {sprint_file.name}")
        
        # Get existing issues
        existing_issues = self._get_existing_issues(sprint_label)
        existing_titles = {issue['title'].lower() for issue in existing_issues}
        
        created_count = 0
        
        # Process each phase
        phases = sprint_data.get('phases', [])
        for phase in phases:
            phase_num = phase.get('phase', 0)
            phase_name = phase.get('name', f'Phase {phase_num}')
            phase_status = phase.get('status', 'pending')
            
            # Skip completed phases unless forced
            if phase_status == 'completed' and not self.verbose:
                continue
            
            tasks = phase.get('tasks', [])
            for task in tasks:
                # Create issue title
                issue_title = f"[Sprint {sprint_number}] Phase {phase_num}: {task}"
                
                # Check if issue already exists
                if issue_title.lower() in existing_titles:
                    if self.verbose:
                        click.echo(f"⏭️  Skipping (exists): {issue_title}")
                    continue
                
                # Create issue body
                issue_body = f"""## Task Description
{task}

## Sprint Information
- **Sprint**: {sprint_title}
- **Sprint ID**: `{sprint_data.get('id', sprint_label)}`
- **Phase**: {phase_num} - {phase_name}
- **Phase Status**: {phase_status}

## Sprint Goals
{chr(10).join(f'- {goal}' for goal in sprint_data.get('goals', ['No goals defined']))}

## Acceptance Criteria
<!-- TODO: Define specific acceptance criteria for this task -->
- [ ] Task implementation complete
- [ ] Tests added/updated
- [ ] Documentation updated

## Implementation Notes
<!-- Add any technical details or considerations here -->

---
_This issue was automatically created from the sprint YAML file. It will be tracked by the sprint automation system._
"""
                
                # Determine labels
                labels = [sprint_label, f"phase-{phase_num}"]
                if phase_status == 'in_progress':
                    labels.append('in-progress')
                elif phase_status == 'blocked':
                    labels.append('blocked')
                
                # Create the issue
                if self._create_issue(issue_title, issue_body, labels):
                    created_count += 1
        
        click.echo(f"\nSummary: Created {created_count} new issues")
        return created_count
    
    def update_sprint_labels(self) -> int:
        """Update labels on existing sprint issues"""
        sprint_file = self._get_sprint_file()
        if not sprint_file:
            click.echo("No active sprint found")
            return 0
        
        # Load sprint data
        try:
            with open(sprint_file, 'r') as f:
                sprint_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return 0
        
        sprint_number = sprint_data.get('sprint_number', 1)
        old_label = f"sprint-current"
        new_label = f"sprint-{sprint_number}"
        
        if self.dry_run:
            click.echo(f"[DRY RUN] Would update labels from '{old_label}' to '{new_label}'")
            return 0
        
        try:
            # Get issues with old label
            cmd = ["gh", "issue", "list", "--label", old_label, "--json", "number", "--limit", "100"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            
            updated_count = 0
            for issue in issues:
                issue_num = issue['number']
                try:
                    # Remove old label
                    subprocess.run(["gh", "issue", "edit", str(issue_num), "--remove-label", old_label], 
                                 capture_output=True, check=True)
                    # Add new label
                    subprocess.run(["gh", "issue", "edit", str(issue_num), "--add-label", new_label], 
                                 capture_output=True, check=True)
                    updated_count += 1
                    if self.verbose:
                        click.echo(f"✓ Updated issue #{issue_num}")
                except Exception as e:
                    click.echo(f"✗ Failed to update issue #{issue_num}: {e}")
            
            click.echo(f"Updated {updated_count} issues with new sprint label")
            return updated_count
            
        except Exception as e:
            click.echo(f"Error updating labels: {e}")
            return 0


@click.group()
def cli():
    """Sprint issue linking tool"""
    pass


@cli.command()
@click.option('--sprint', help='Specific sprint ID')
@click.option('--dry-run', is_flag=True, help='Show what would be done without creating issues')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def create(sprint, dry_run, verbose):
    """Create GitHub issues from sprint tasks"""
    linker = SprintIssueLinker(sprint_id=sprint, dry_run=dry_run, verbose=verbose)
    count = linker.create_issues_from_sprint()
    sys.exit(0 if count >= 0 else 1)


@cli.command()
@click.option('--sprint', help='Specific sprint ID')
@click.option('--dry-run', is_flag=True, help='Show what would be done without updating')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def update_labels(sprint, dry_run, verbose):
    """Update sprint labels on existing issues"""
    linker = SprintIssueLinker(sprint_id=sprint, dry_run=dry_run, verbose=verbose)
    count = linker.update_sprint_labels()
    sys.exit(0 if count >= 0 else 1)


if __name__ == '__main__':
    cli()