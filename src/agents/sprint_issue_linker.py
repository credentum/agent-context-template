#!/usr/bin/env python3
"""
Sprint Issue Linker - Creates GitHub issues from sprint tasks

This script helps create GitHub issues that are properly linked
to sprint tasks for automated tracking.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
        self.templates_dir = Path(".github/ISSUE_TEMPLATE")
        self._check_gh_cli()

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input to prevent command injection"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Remove only the most dangerous characters that could cause command injection
        # Keep common markdown characters like [], (), {}, <>, etc.
        # Only remove: backticks, dollar signs, backslashes, semicolons, pipes, ampersands
        sanitized = re.sub(r"[`$\\;|&]", "", str(text))

        # Limit length to prevent excessively long inputs
        if len(sanitized) > 2000:
            sanitized = sanitized[:1997] + "..."

        return sanitized.strip()

    def _validate_label(self, label: str) -> str:
        """Validate and sanitize GitHub label"""
        if not isinstance(label, str):
            raise ValueError("Label must be a string")

        # GitHub labels: alphanumeric, hyphens, underscores, periods, colons
        sanitized = re.sub(r"[^a-zA-Z0-9\-_.:']", "", str(label))

        if not sanitized:
            raise ValueError("Label contains no valid characters")

        if len(sanitized) > 50:
            sanitized = sanitized[:50]

        return sanitized

    def _validate_issue_number(self, issue_num: Any) -> int:
        """Validate that issue number is a safe integer"""
        try:
            num = int(issue_num)
            if num <= 0 or num > 999999:  # Reasonable bounds
                raise ValueError(f"Issue number out of range: {num}")
            return num
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid issue number: {issue_num}") from e

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

    def _get_template_for_task(self, task: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Determine which template to use based on task properties"""
        # Only check for templates if task is in dict format
        if not isinstance(task, dict):
            return None

        # Check if task explicitly specifies a template
        if task.get("template"):
            template_name = task["template"]
            if template_name == "investigation":
                return "investigation.md"
            elif template_name == "sprint-task":
                return "sprint-task.md"

        # Check if task indicates unclear scope
        description = task.get("description", "").lower()
        title = task.get("title", "").lower()

        # Keywords that suggest investigation is needed
        investigation_keywords = [
            "investigate",
            "unclear",
            "unknown",
            "research",
            "find out",
            "determine",
            "analyze",
            "discover",
            "root cause",
            "debug",
            "diagnose",
            "scope",
        ]

        for keyword in investigation_keywords:
            if keyword in description or keyword in title:
                if self.verbose:
                    click.echo(f"  Auto-detected investigation task (keyword: {keyword})")
                return "investigation.md"

        # Default to sprint task template for sprint tasks
        return "sprint-task.md"

    def _create_issue(
        self, title: str, body: str, labels: List[str], template: Optional[str] = None
    ) -> Optional[int]:
        """Create a GitHub issue, optionally noting the template used"""
        # Sanitize all inputs
        safe_title = self._sanitize_text(title)
        safe_body = self._sanitize_text(body)
        safe_labels = [self._validate_label(label) for label in labels]

        # Add template reference to body if provided
        if template:
            template_note = f"<!-- Created from template: {template} -->\n\n"
            safe_body = template_note + safe_body

        if self.dry_run:
            click.echo(f"[DRY RUN] Would create issue: {safe_title}")
            if self.verbose:
                click.echo(f"  Labels: {', '.join(safe_labels)}")
                if template:
                    click.echo(f"  Template: {template}")
                click.echo(f"  Body preview: {safe_body[:200]}...")
            return None

        try:
            cmd = ["gh", "issue", "create", "--title", safe_title, "--body", safe_body]
            # Batch all labels in a single --label argument to reduce API calls
            if safe_labels:
                labels_str = ",".join(safe_labels)
                cmd.extend(["--label", labels_str])

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Extract issue number from output
            if result.stdout:
                # Output typically includes the issue URL
                parts = result.stdout.strip().split("/")
                issue_number = int(parts[-1])
                click.echo(f"✓ Created issue #{issue_number}: {title}")
                if template and self.verbose:
                    click.echo(f"  Using template guidance: {template}")
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
                    # Old format - just a string (validate input)
                    task_text = self._sanitize_text(task)
                    task_title = f"[Sprint {sprint_number}] Phase {phase_num}: {task_text}"
                    task_description = task_text
                    task_labels = [sprint_label, f"phase-{phase_num}"]
                    task_dependencies = []
                else:
                    # New format - detailed task object (validate all inputs)
                    raw_title = task.get("title", "Untitled Task")
                    raw_description = task.get("description", "No description provided")

                    sanitized_title = self._sanitize_text(raw_title)
                    task_title = f"[Sprint {sprint_number}] Phase {phase_num}: {sanitized_title}"
                    task_description = self._sanitize_text(raw_description)

                    # Validate labels
                    raw_labels = task.get("labels", [sprint_label, f"phase-{phase_num}"])
                    task_labels = [self._validate_label(label) for label in raw_labels if label]

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
_Auto-created from sprint YAML and tracked by sprint system._
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
_Auto-created from sprint YAML and tracked by sprint system._
"""

                # Add phase status to labels
                if phase_status == "in_progress":
                    task_labels.append("in-progress")
                elif phase_status == "blocked":
                    task_labels.append("blocked")

                # Determine template for task
                template = self._get_template_for_task(task)

                # Add investigation label if using investigation template
                if template == "investigation.md" and "investigation" not in task_labels:
                    task_labels.append("investigation")

                # Create the issue with template reference
                issue_number = self._create_issue(task_title, issue_body, task_labels, template)
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
            # Sanitize label inputs
            safe_old_label = self._validate_label(old_label)
            safe_new_label = self._validate_label(new_label)

            # Get issues with old label
            cmd = [
                "gh",
                "issue",
                "list",
                "--label",
                safe_old_label,
                "--json",
                "number",
                "--limit",
                "100",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)

            updated_count = 0
            for issue in issues:
                # Validate issue number from API response
                issue_num = self._validate_issue_number(issue["number"])
                try:
                    # Remove old label
                    subprocess.run(
                        ["gh", "issue", "edit", str(issue_num), "--remove-label", safe_old_label],
                        capture_output=True,
                        check=True,
                    )
                    # Add new label
                    subprocess.run(
                        ["gh", "issue", "edit", str(issue_num), "--add-label", safe_new_label],
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

    def _get_current_issue_state(self, issue_number: int) -> str:
        """Get current GitHub issue state (open/closed)"""
        try:
            cmd = ["gh", "issue", "view", str(issue_number), "--json", "state"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            state = data.get("state", "open")
            return str(state).lower()
        except Exception as e:
            if self.verbose:
                click.echo(f"Warning: Could not get state for issue #{issue_number}: {e}")
            return "unknown"

    def _get_current_issue_labels(self, issue_number: int) -> List[str]:
        """Get current GitHub issue labels"""
        try:
            cmd = ["gh", "issue", "view", str(issue_number), "--json", "labels"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return [label["name"] for label in data.get("labels", [])]
        except Exception as e:
            if self.verbose:
                click.echo(f"Warning: Could not get labels for issue #{issue_number}: {e}")
            return []

    def _update_issue_state(self, issue_number: int, new_state: str, reason: str = "") -> bool:
        """Open or close GitHub issue"""
        if new_state not in ["open", "closed"]:
            raise ValueError(f"Invalid issue state: {new_state}")

        if self.dry_run:
            action = "close" if new_state == "closed" else "reopen"
            click.echo(f"[DRY RUN] Would {action} issue #{issue_number}")
            if reason:
                click.echo(f"  Reason: {reason}")
            return True

        try:
            if new_state == "closed":
                cmd = ["gh", "issue", "close", str(issue_number)]
                if reason:
                    cmd.extend(["--comment", self._sanitize_text(reason)])
            else:
                cmd = ["gh", "issue", "reopen", str(issue_number)]
                if reason:
                    cmd.extend(["--comment", self._sanitize_text(reason)])

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            action = "closed" if new_state == "closed" else "reopened"
            if self.verbose:
                click.echo(f"✓ {action.title()} issue #{issue_number}")
            return True
        except Exception as e:
            click.echo(f"✗ Failed to update state for issue #{issue_number}: {e}")
            return False

    def _calculate_task_labels(
        self, task: Dict[str, Any], phase: Dict[str, Any], sprint_data: Dict[str, Any]
    ) -> List[str]:
        """Calculate target labels for a task based on sprint, phase, and task data"""
        labels = set()

        # Sprint-level labels
        sprint_number = sprint_data.get("sprint_number", 1)
        labels.add(f"sprint-{sprint_number}")

        # Default labels from config
        config = sprint_data.get("config", {})
        default_labels = config.get("default_labels", [])
        labels.update(default_labels)

        # Phase-based labels
        phase_num = phase.get("phase", 1)
        labels.add(f"phase-{phase_num}")

        # Phase status labels
        phase_status = phase.get("status", "pending")
        if phase_status == "blocked":
            labels.add("blocked")
        elif phase_status == "in_progress":
            labels.add("in-progress")

        # Phase component and priority
        if phase.get("component"):
            labels.add(f"component:{phase['component']}")
        if phase.get("priority"):
            labels.add(f"priority:{phase['priority']}")

        # Task-specific labels
        task_labels = task.get("labels", [])
        labels.update(task_labels)

        # Validate all labels and return sorted list
        validated_labels = []
        for label in labels:
            try:
                validated_labels.append(self._validate_label(str(label)))
            except ValueError:
                if self.verbose:
                    click.echo(f"Warning: Skipping invalid label: {label}")
                continue

        return sorted(validated_labels)

    def _sync_issue_labels(self, issue_number: int, target_labels: List[str]) -> bool:
        """Sync GitHub issue labels with target state"""
        current_labels = self._get_current_issue_labels(issue_number)
        target_set = set(target_labels)
        current_set = set(current_labels)

        # Calculate changes needed
        labels_to_add = target_set - current_set
        labels_to_remove = current_set - target_set

        # Only remove sprint-related labels to preserve other labels
        sprint_prefixes = ("sprint-", "phase-", "component:", "priority:", "blocked", "in-progress")
        labels_to_remove = {
            label
            for label in labels_to_remove
            if any(label.startswith(prefix) for prefix in sprint_prefixes)
        }

        if not labels_to_add and not labels_to_remove:
            return True  # No changes needed

        if self.dry_run:
            if labels_to_add:
                labels_str = ", ".join(labels_to_add)
                click.echo(f"[DRY RUN] Would add labels to issue #{issue_number}: {labels_str}")
            if labels_to_remove:
                labels_str = ", ".join(labels_to_remove)
                click.echo(
                    f"[DRY RUN] Would remove labels from issue #{issue_number}: {labels_str}"
                )
            return True

        success = True
        try:
            # Batch add labels in single command
            if labels_to_add:
                add_labels_str = ",".join(labels_to_add)
                cmd = ["gh", "issue", "edit", str(issue_number), "--add-label", add_labels_str]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Batch remove labels in single command
            if labels_to_remove:
                remove_labels_str = ",".join(labels_to_remove)
                cmd = [
                    "gh",
                    "issue",
                    "edit",
                    str(issue_number),
                    "--remove-label",
                    remove_labels_str,
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

            if self.verbose and (labels_to_add or labels_to_remove):
                click.echo(f"✓ Updated labels for issue #{issue_number}")

        except Exception as e:
            click.echo(f"✗ Failed to update labels for issue #{issue_number}: {e}")
            success = False

        return success

    def _find_orphaned_issues(
        self, existing_issues: List[Dict[str, Any]], current_tasks: List[Dict[str, Any]]
    ) -> List[int]:
        """Find GitHub issues for tasks no longer in sprint"""
        # Get all current task GitHub issue numbers
        current_issue_numbers = set()
        for task in current_tasks:
            if isinstance(task, dict) and task.get("github_issue"):
                current_issue_numbers.add(task["github_issue"])

        # Find existing issues not in current tasks
        orphaned = []
        for issue in existing_issues:
            issue_number = issue["number"]
            if issue_number not in current_issue_numbers:
                orphaned.append(issue_number)

        return orphaned

    def _close_orphaned_issue(self, issue_number: int, reason: str) -> bool:
        """Close orphaned issue with explanatory comment"""
        comment = f"""🤖 **Automated Sprint Sync**

{reason}

This issue was automatically closed because the corresponding task is no longer present in the
sprint YAML file. If this was done in error, please:

1. Re-add the task to the sprint YAML, or
2. Manually reopen this issue if it should remain independent

---
_Automated by sprint bidirectional sync system_"""

        return self._update_issue_state(issue_number, "closed", comment)

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
        all_current_tasks = []  # Track all tasks for orphan detection

        # Process each phase
        phases = sprint_data.get("phases", [])
        for phase in phases:
            phase_status = phase.get("status", "pending")
            tasks = phase.get("tasks", [])

            for task in tasks:
                if not isinstance(task, dict):
                    continue  # Skip old format tasks

                all_current_tasks.append(task)  # Track for orphan detection
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
                    issue_number = github_issue["number"]

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
                            chr(10).join(f"- {dep}" for dep in deps_list) if deps_list else "- None"
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
_Auto-created from sprint YAML and tracked by sprint system._
"""
                        update_fields["body"] = issue_body
                        need_update = True

                    # Update issue if needed
                    if need_update and not self.dry_run:
                        try:
                            # Validate issue number from API response
                            issue_num = self._validate_issue_number(github_issue["number"])
                            cmd = ["gh", "issue", "edit", str(issue_num)]

                            # Sanitize update field values
                            for field, value in update_fields.items():
                                if field in ["title", "body"]:
                                    safe_value = self._sanitize_text(value)
                                elif field == "state":
                                    # Only allow valid GitHub issue states
                                    if value not in ["open", "closed"]:
                                        raise ValueError(f"Invalid issue state: {value}")
                                    safe_value = value
                                else:
                                    # Skip unknown fields for security
                                    continue
                                cmd.extend([f"--{field}", safe_value])

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

                    # NEW: Sync issue state based on phase status
                    current_state = self._get_current_issue_state(issue_number)
                    target_state = "closed" if phase_status == "completed" else "open"

                    if current_state != "unknown" and current_state != target_state:
                        reason = (
                            f"Phase '{phase.get('name', '')}' marked as completed"
                            if target_state == "closed"
                            else f"Phase '{phase.get('name', '')}' status changed to {phase_status}"
                        )
                        if self._update_issue_state(issue_number, target_state, reason):
                            sync_count += 1

                    # NEW: Sync issue labels
                    target_labels = self._calculate_task_labels(task, phase, sprint_data)
                    if self._sync_issue_labels(issue_number, target_labels):
                        if self.verbose:
                            pass  # Already logged in _sync_issue_labels

                else:
                    # Create new issue for task without GitHub issue
                    if not task.get("github_issue"):
                        task_description = task.get("description", "No description provided")
                        task_labels = self._calculate_task_labels(task, phase, sprint_data)

                        deps_list = task.get("dependencies", [])
                        deps_str = (
                            chr(10).join(f"- {dep}" for dep in deps_list) if deps_list else "- None"
                        )
                        issue_body = f"""{task_description}

## Sprint Information
- **Sprint**: {sprint_title}
- **Sprint ID**: `{sprint_data.get('id', sprint_label)}`
- **Phase**: {phase.get('phase', '')} - {phase.get('name', '')}
- **Phase Status**: {phase.get('status', 'pending')}

## Dependencies
{deps_str}

---
_Auto-created from sprint YAML and tracked by sprint system._
"""

                        issue_number = self._create_issue(task_title, issue_body, task_labels)
                        if issue_number:
                            task["github_issue"] = issue_number
                            changes_made = True
                            sync_count += 1

                            # NEW: Set initial state for new issue based on phase status
                            if phase_status == "completed":
                                reason = f"Created in completed phase '{phase.get('name', '')}'"
                                self._update_issue_state(issue_number, "closed", reason)

        # NEW: Handle orphaned issues (tasks removed from sprint)
        orphaned_issues = self._find_orphaned_issues(existing_issues, all_current_tasks)
        for issue_number in orphaned_issues:
            if self._close_orphaned_issue(issue_number, "Task removed from sprint YAML"):
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
        if orphaned_issues:
            click.echo(f"Closed {len(orphaned_issues)} orphaned issues: {orphaned_issues}")
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
    """Create GitHub issues from sprint tasks

    Automatically selects appropriate issue templates:
    - Investigation template for unclear scope tasks
    - Sprint task template for standard tasks

    Tasks can specify template: "investigation" or "sprint-task"
    """
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
