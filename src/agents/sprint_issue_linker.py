#!/usr/bin/env python3
"""
Sprint Issue Linker - Creates GitHub issues from sprint tasks

This script helps create GitHub issues that are properly linked
to sprint tasks for automated tracking.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml


class SprintIssueLinker:
    """Links sprint tasks with GitHub issues"""

    def __init__(
        self, sprint_id: Optional[str] = None, dry_run: bool = False, verbose: bool = False
    ):
        self.sprint_id = sprint_id
        self.dry_run = dry_run
        self.verbose = verbose
        self.context_dir = Path("context")
        self.sprints_dir = self.context_dir / "sprints"
        self._check_gh_cli()

    def _check_gh_cli(self) -> None:
        """Check if GitHub CLI is available and authenticated"""
        if self.dry_run:
            return  # Skip check in dry-run mode

        try:
            subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
            if self.verbose:
                click.echo("✓ GitHub CLI authenticated")
        except FileNotFoundError:
            click.echo("Error: GitHub CLI not found. Please install: https://cli.github.com/")
            sys.exit(1)
        except subprocess.CalledProcessError:
            click.echo("Error: GitHub CLI not authenticated. Run: gh auth login")
            sys.exit(1)

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
                    with open(sprint_file, "r") as f:
                        data = yaml.safe_load(f)
                    if data.get("status") in ["planning", "in_progress"]:
                        return sprint_file
                except Exception:
                    continue
        return None

    def _get_existing_issues(self, sprint_label: str) -> List[Dict[str, Any]]:
        """Get existing issues with the sprint label"""
        try:
            cmd = [
                "gh",
                "issue",
                "list",
                "--label",
                sprint_label,
                "--json",
                "number,title,state,body",
                "--limit",
                "100",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            return issues if isinstance(issues, list) else []
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
                parts = result.stdout.strip().split("/")
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
            with open(sprint_file, "r") as f:
                sprint_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return 0

        sprint_number = sprint_data.get("sprint_number", 1)
        sprint_label = f"sprint-{sprint_number}"
        sprint_title = sprint_data.get("title", f"Sprint {sprint_number}")

        click.echo(f"Processing {sprint_title} from {sprint_file.name}")

        # Get existing issues
        existing_issues = self._get_existing_issues(sprint_label)
        existing_titles = {issue["title"].lower() for issue in existing_issues}

        created_count = 0

        # Process each phase
        phases = sprint_data.get("phases", [])
        for phase in phases:
            phase_num = phase.get("phase", 0)
            phase_name = phase.get("name", f"Phase {phase_num}")
            phase_status = phase.get("status", "pending")

            # Skip completed phases unless forced
            if phase_status == "completed" and not self.verbose:
                continue

            tasks = phase.get("tasks", [])
            for task in tasks:
                # Handle both old format (string) and new format (dict)
                if isinstance(task, str):
                    # Old format - just a string
                    task_title = f"[Sprint {sprint_number}] Phase {phase_num}: {task}"
                    task_description = task
                    task_labels = [sprint_label, f"phase-{phase_num}"]
                    task_dependencies = []
                else:
                    # New format - detailed task object
                    task_title = task.get(
                        "title", f"[Sprint {sprint_number}] Phase {phase_num}: Untitled Task"
                    )
                    task_description = task.get("description", "No description provided")
                    task_labels = task.get("labels", [sprint_label, f"phase-{phase_num}"])
                    task_dependencies = task.get("dependencies", [])

                    # Skip if already has a GitHub issue assigned
                    if task.get("github_issue"):
                        if self.verbose:
                            click.echo(
                                f"⏭️  Skipping (has issue #{task['github_issue']}): {task_title}"
                            )
                        continue

                # Check if issue already exists by title
                if task_title.lower() in existing_titles:
                    if self.verbose:
                        click.echo(f"⏭️  Skipping (exists): {task_title}")
                    continue

                # Create enhanced issue body
                if isinstance(task, dict):
                    # Use the description from the task if it's in new format
                    deps_text = (
                        chr(10).join(f"- {dep}" for dep in task_dependencies)
                        if task_dependencies
                        else "- None"
                    )
                    issue_body = f"""{task_description}

## Sprint Information
- **Sprint**: {sprint_title}
- **Sprint ID**: `{sprint_data.get('id', sprint_label)}`
- **Phase**: {phase_num} - {phase_name}
- **Phase Status**: {phase_status}

## Dependencies
{deps_text}

---
_This issue was automatically created from the sprint YAML file and is tracked by the automated sprint system._
"""
                else:
                    # Old format fallback
                    issue_body = f"""## Task Description
{task_description}

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
_This issue was automatically created from the sprint YAML file and is tracked by the automated sprint system._
"""

                # Add phase status to labels
                if phase_status == "in_progress":
                    task_labels.append("in-progress")
                elif phase_status == "blocked":
                    task_labels.append("blocked")

                # Create the issue
                issue_number = self._create_issue(task_title, issue_body, task_labels)
                if issue_number:
                    created_count += 1

                    # Update sprint file with issue number if in new format
                    if isinstance(task, dict) and not self.dry_run:
                        task["github_issue"] = issue_number

        # Save updated sprint file with issue numbers
        if created_count > 0 and not self.dry_run:
            try:
                with open(sprint_file, "w") as f:
                    yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False)
                click.echo(f"✓ Updated {sprint_file.name} with issue numbers")
            except Exception as e:
                click.echo(f"⚠️  Warning: Could not update sprint file: {e}")

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
            with open(sprint_file, "r") as f:
                sprint_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return 0

        sprint_number = sprint_data.get("sprint_number", 1)
        old_label = "sprint-current"
        new_label = f"sprint-{sprint_number}"

        if self.dry_run:
            click.echo(f"[DRY RUN] Would update labels from '{old_label}' to '{new_label}'")
            return 0

        try:
            # Get issues with old label
            cmd = [
                "gh",
                "issue",
                "list",
                "--label",
                old_label,
                "--json",
                "number",
                "--limit",
                "100",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)

            updated_count = 0
            for issue in issues:
                issue_num = issue["number"]
                try:
                    # Remove old label
                    subprocess.run(
                        ["gh", "issue", "edit", str(issue_num), "--remove-label", old_label],
                        capture_output=True,
                        check=True,
                    )
                    # Add new label
                    subprocess.run(
                        ["gh", "issue", "edit", str(issue_num), "--add-label", new_label],
                        capture_output=True,
                        check=True,
                    )
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

    def sync_sprint_with_issues(self) -> int:
        """Sync sprint YAML with GitHub issues bidirectionally"""
        sprint_file = self._get_sprint_file()
        if not sprint_file:
            click.echo("No active sprint found")
            return 0

        # Load sprint data
        try:
            with open(sprint_file, "r") as f:
                sprint_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return 0

        sprint_number = sprint_data.get("sprint_number", 1)
        sprint_label = f"sprint-{sprint_number}"
        sprint_title = sprint_data.get("title", f"Sprint {sprint_number}")

        click.echo(f"Syncing {sprint_title} from {sprint_file.name}")

        # Get existing issues
        existing_issues = self._get_existing_issues(sprint_label)
        existing_by_number = {issue["number"]: issue for issue in existing_issues}
        existing_by_title = {issue["title"].lower(): issue for issue in existing_issues}

        sync_count = 0
        changes_made = False

        # Process each phase
        phases = sprint_data.get("phases", [])
        for phase in phases:
            tasks = phase.get("tasks", [])
            for task in tasks:
                if not isinstance(task, dict):
                    continue  # Skip old format tasks

                task_title = task.get("title", "")
                existing_issue_num = task.get("github_issue")

                # Find corresponding GitHub issue
                github_issue = None
                if existing_issue_num and existing_issue_num in existing_by_number:
                    github_issue = existing_by_number[existing_issue_num]
                elif task_title.lower() in existing_by_title:
                    github_issue = existing_by_title[task_title.lower()]
                    # Update sprint with found issue number
                    if not existing_issue_num:
                        task["github_issue"] = github_issue["number"]
                        changes_made = True

                if github_issue:
                    # Check if we need to update the issue
                    need_update = False
                    update_fields = {}

                    # Check title
                    if github_issue["title"] != task_title:
                        update_fields["title"] = task_title
                        need_update = True

                    # Check description (body)
                    task_description = task.get("description", "")
                    if task_description and github_issue.get("body", "") != task_description:
                        # Create enhanced issue body
                        deps_list = task.get("dependencies", [])
                        deps_text = (
                            chr(10).join(f"- {dep}" for dep in deps_list)
                            if deps_list
                            else "- None"
                        )
                        issue_body = f"""{task_description}

## Sprint Information
- **Sprint**: {sprint_title}
- **Sprint ID**: `{sprint_data.get('id', sprint_label)}`
- **Phase**: {phase.get('phase', '')} - {phase.get('name', '')}
- **Phase Status**: {phase.get('status', 'pending')}

## Dependencies
{deps_text}

---
_This issue was automatically created from the sprint YAML file and is tracked by the automated sprint system._
"""
                        update_fields["body"] = issue_body
                        need_update = True

                    # Update issue if needed
                    if need_update and not self.dry_run:
                        try:
                            cmd = ["gh", "issue", "edit", str(github_issue["number"])]
                            for field, value in update_fields.items():
                                cmd.extend([f"--{field}", value])

                            subprocess.run(cmd, capture_output=True, text=True, check=True)
                            sync_count += 1
                            if self.verbose:
                                click.echo(
                                    f"✓ Updated issue #{github_issue['number']}: {task_title}"
                                )
                        except Exception as e:
                            click.echo(f"✗ Failed to update issue #{github_issue['number']}: {e}")
                    elif need_update and self.dry_run:
                        click.echo(
                            f"[DRY RUN] Would update issue #{github_issue['number']}: {task_title}"
                        )
                        sync_count += 1

                else:
                    # Create new issue for task without GitHub issue
                    if not task.get("github_issue"):
                        task_description = task.get("description", "No description provided")
                        task_labels = task.get("labels", [sprint_label])

                        issue_body = f"""{task_description}

## Sprint Information
- **Sprint**: {sprint_title}
- **Sprint ID**: `{sprint_data.get('id', sprint_label)}`
- **Phase**: {phase.get('phase', '')} - {phase.get('name', '')}
- **Phase Status**: {phase.get('status', 'pending')}

## Dependencies
{chr(10).join(f'- {dep}' for dep in task.get('dependencies', [])) if task.get('dependencies') else '- None'}

---
_This issue was automatically created from the sprint YAML file and is tracked by the automated sprint system._
"""

                        issue_number = self._create_issue(task_title, issue_body, task_labels)
                        if issue_number:
                            task["github_issue"] = issue_number
                            changes_made = True
                            sync_count += 1

        # Save updated sprint file if changes were made
        if changes_made and not self.dry_run:
            try:
                with open(sprint_file, "w") as f:
                    yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False)
                click.echo(f"✓ Updated {sprint_file.name} with sync changes")
            except Exception as e:
                click.echo(f"⚠️  Warning: Could not update sprint file: {e}")

        click.echo(f"\nSync Summary: {sync_count} items processed")
        return sync_count


@click.group()
def cli():
    """Sprint issue linking tool"""
    pass


@cli.command()
@click.option("--sprint", help="Specific sprint ID")
@click.option("--dry-run", is_flag=True, help="Show what would be done without creating issues")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def create(sprint, dry_run, verbose):
    """Create GitHub issues from sprint tasks"""
    linker = SprintIssueLinker(sprint_id=sprint, dry_run=dry_run, verbose=verbose)
    count = linker.create_issues_from_sprint()
    sys.exit(0 if count >= 0 else 1)


@cli.command()
@click.option("--sprint", help="Specific sprint ID")
@click.option("--dry-run", is_flag=True, help="Show what would be done without updating")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def update_labels(sprint, dry_run, verbose):
    """Update sprint labels on existing issues"""
    linker = SprintIssueLinker(sprint_id=sprint, dry_run=dry_run, verbose=verbose)
    count = linker.update_sprint_labels()
    sys.exit(0 if count >= 0 else 1)


@cli.command()
@click.option("--sprint", help="Specific sprint ID")
@click.option("--dry-run", is_flag=True, help="Show what would be done without syncing")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def sync(sprint, dry_run, verbose):
    """Sync sprint YAML with GitHub issues bidirectionally"""
    linker = SprintIssueLinker(sprint_id=sprint, dry_run=dry_run, verbose=verbose)
    count = linker.sync_sprint_with_issues()
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    cli()
