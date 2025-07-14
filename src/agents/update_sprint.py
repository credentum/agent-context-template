#!/usr/bin/env python3
"""
Sprint Update Agent for the Agent-First Context System

This agent automatically updates sprint documents based on:
- Task completion status from GitHub issues
- Phase progress tracking
- Timestamp updates
- Integration with GitHub Actions
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml


class SprintUpdater:
    """Agent responsible for sprint document updates"""

    def __init__(self, sprint_id: Optional[str] = None, verbose: bool = False):
        self.verbose = verbose
        self.context_dir = Path("context")
        self.sprints_dir = self.context_dir / "sprints"
        self.sprint_id = sprint_id
        self.updates_made: list[str] = []
        self.config = self._load_config()
        self._check_gh_cli()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(".ctxrc.yaml", "r") as f:
                config = yaml.safe_load(f)
                return config if isinstance(config, dict) else {}
        except Exception as e:
            if self.verbose:
                click.echo(f"Warning: Could not load .ctxrc.yaml: {e}")
            return {"agents": {"pm_agent": {"sprint_duration_days": 14}}}

    def _check_gh_cli(self) -> None:
        """Check if GitHub CLI is available and authenticated"""
        try:
            subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
            if self.verbose:
                click.echo("✓ GitHub CLI authenticated")
        except FileNotFoundError:
            if self.verbose:
                click.echo("⚠️  GitHub CLI not found, issue tracking will be limited")
        except subprocess.CalledProcessError:
            if self.verbose:
                click.echo("⚠️  GitHub CLI not authenticated, issue tracking will be limited")

    def _get_current_sprint(self) -> Optional[Path]:
        """Find the current active sprint document"""
        if self.sprint_id:
            # Specific sprint requested
            sprint_file = self.sprints_dir / f"{self.sprint_id}.yaml"
            if sprint_file.exists():
                return sprint_file
            else:
                click.echo(f"Error: Sprint file not found: {sprint_file}")
                return None

        # Find most recent active sprint
        active_sprints = []
        for sprint_file in self.sprints_dir.glob("*.yaml"):
            try:
                with open(sprint_file, "r") as f:
                    data = yaml.safe_load(f)

                if data and data.get("status") in ["planning", "in_progress", "active"]:
                    active_sprints.append((sprint_file, data))
            except Exception:
                continue

        if not active_sprints:
            click.echo("No active sprints found")
            return None

        # Return the most recent by sprint number
        active_sprints.sort(key=lambda x: x[1].get("sprint_number", 0), reverse=True)
        return active_sprints[0][0]

    def _get_github_issues(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch GitHub issues for the current repository"""
        try:
            cmd = ["gh", "issue", "list", "--json", "number,title,state,labels,body"]
            if label:
                cmd.extend(["--label", label])

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            return issues if isinstance(issues, list) else []
        except subprocess.CalledProcessError as e:
            if self.verbose:
                click.echo(f"Error fetching GitHub issues: {e}")
            return []
        except json.JSONDecodeError as e:
            if self.verbose:
                click.echo(f"Error parsing GitHub issues JSON: {e}")
            return []
        except FileNotFoundError as e:
            if self.verbose:
                click.echo(f"GitHub CLI not found: {e}")
            return []

    def _match_task_to_issue(self, task: str, issue_title: str) -> bool:
        """Match task to issue using normalized comparison"""
        import re

        # Normalize both strings: remove punctuation, extra spaces
        def normalize(text: str) -> str:
            # Remove special characters but keep alphanumeric and spaces
            text = re.sub(r"[^\w\s]", " ", text.lower())
            # Collapse multiple spaces
            text = re.sub(r"\s+", " ", text)
            return text.strip()

        normalized_task = normalize(task)
        normalized_title = normalize(issue_title)

        # Check if the task appears as a distinct phrase in the title
        # This prevents "test" from matching "integration tests completed"
        task_words = normalized_task.split()
        title_words = normalized_title.split()

        # Look for exact sequence of words
        for i in range(len(title_words) - len(task_words) + 1):
            if title_words[i : i + len(task_words)] == task_words:
                return True

        return False

    def _update_phase_status(
        self, phases: List[Dict[str, Any]], issues: List[Dict[str, Any]]
    ) -> bool:
        """Update phase status based on task completion"""
        updated = False

        for phase in phases:
            if phase["status"] == "completed":
                continue

            tasks = phase.get("tasks", [])
            if not tasks:
                continue

            # Check if all tasks are mentioned in closed issues
            completed_tasks = 0
            for task in tasks:
                # Improved matching - look for task text in closed issues
                for issue in issues:
                    if issue["state"] == "CLOSED" and self._match_task_to_issue(
                        task, issue["title"]
                    ):
                        completed_tasks += 1
                        break

            # Update phase status based on task completion
            if completed_tasks == len(tasks) and phase["status"] != "completed":
                phase["status"] = "completed"
                self.updates_made.append(f"Phase {phase['phase']} marked as completed")
                updated = True
            elif completed_tasks > 0 and phase["status"] == "pending":
                phase["status"] = "in_progress"
                self.updates_made.append(f"Phase {phase['phase']} marked as in_progress")
                updated = True

        return updated

    def _update_sprint_status(self, data: Dict[str, Any]) -> bool:
        """Update overall sprint status based on phase completion"""
        phases = data.get("phases", [])
        if not phases:
            return False

        all_completed = all(p["status"] == "completed" for p in phases)
        any_in_progress = any(p["status"] == "in_progress" for p in phases)

        updated = False
        current_status = data.get("status")

        if all_completed and current_status != "completed":
            data["status"] = "completed"
            self.updates_made.append("Sprint marked as completed")
            updated = True
        elif any_in_progress and current_status == "planning":
            data["status"] = "in_progress"
            self.updates_made.append("Sprint marked as in_progress")
            updated = True

        return updated

    def _update_timestamps(self, data: Dict[str, Any]) -> bool:
        """Update last_modified and last_referenced timestamps"""
        today = datetime.now().strftime("%Y-%m-%d")
        updated = False

        if data.get("last_modified") != today:
            data["last_modified"] = today
            updated = True

        if data.get("last_referenced") != today:
            data["last_referenced"] = today
            updated = True

        return updated

    def _create_next_sprint(self, current_data: Dict[str, Any]) -> Optional[Path]:
        """Create the next sprint document when current sprint is completed"""
        if current_data.get("status") != "completed":
            return None

        sprint_number = current_data.get("sprint_number", 0) + 1
        sprint_id = f"sprint-{sprint_number:03d}"
        new_sprint_path = self.sprints_dir / f"{sprint_id}.yaml"

        if new_sprint_path.exists():
            if self.verbose:
                click.echo(f"Next sprint already exists: {new_sprint_path}")
            return None

        # Calculate dates
        duration_days = (
            self.config.get("agents", {}).get("pm_agent", {}).get("sprint_duration_days", 14)
        )
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)

        new_sprint_data = {
            "schema_version": "1.0.0",
            "document_type": "sprint",
            "id": sprint_id,
            "title": f"Sprint {sprint_number}",
            "status": "planning",
            "created_date": start_date.strftime("%Y-%m-%d"),
            "sprint_number": sprint_number,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "last_modified": start_date.strftime("%Y-%m-%d"),
            "last_referenced": start_date.strftime("%Y-%m-%d"),
            "goals": ["[To be defined]"],
            "phases": [],
            "team": current_data.get("team", []),
            "success_metrics": current_data.get("success_metrics", []),
        }

        # Add graph metadata if present
        if "graph_metadata" in current_data:
            new_sprint_data["graph_metadata"] = current_data["graph_metadata"]

        with open(new_sprint_path, "w") as f:
            yaml.dump(new_sprint_data, f, default_flow_style=False, sort_keys=False)

        self.updates_made.append(f"Created next sprint: {sprint_id}")
        return new_sprint_path

    def update_sprint(self) -> bool:
        """Main method to update sprint document"""
        sprint_file = self._get_current_sprint()
        if not sprint_file:
            return False

        if self.verbose:
            click.echo(f"Updating sprint: {sprint_file.name}")

        # Load sprint data
        try:
            with open(sprint_file, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading sprint file: {e}")
            return False

        # Get GitHub issues
        sprint_label = f"sprint-{data.get('sprint_number', 1)}"
        issues = self._get_github_issues(label=sprint_label)

        # Perform updates
        updated = False

        # Update phase status based on issues
        if self._update_phase_status(data.get("phases", []), issues):
            updated = True

        # Update sprint status
        if self._update_sprint_status(data):
            updated = True

        # Update timestamps
        if self._update_timestamps(data):
            updated = True

        # Save updates
        if updated:
            with open(sprint_file, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            if self.verbose:
                click.echo(f"Sprint updated with {len(self.updates_made)} changes")
                for update in self.updates_made:
                    click.echo(f"  - {update}")
        else:
            if self.verbose:
                click.echo("No updates needed")

        # Create next sprint if current is completed
        if data.get("status") == "completed":
            self._create_next_sprint(data)

        return updated

    def generate_report(self) -> str:
        """Generate a sprint status report"""
        sprint_file = self._get_current_sprint()
        if not sprint_file:
            return "No active sprint found"

        try:
            with open(sprint_file, "r") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            return f"Error loading sprint: {e}"

        report = []
        report.append(f"# {data.get('title', 'Sprint Report')}")
        report.append(f"**Status**: {data.get('status', 'unknown')}")
        report.append(f"**Period**: {data.get('start_date')} to {data.get('end_date')}")
        report.append("")

        # Phase summary
        phases = data.get("phases", [])
        if phases:
            report.append("## Phase Progress")
            for phase in phases:
                status_emoji = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "pending": "⏳",
                    "blocked": "🚫",
                }.get(phase["status"], "❓")

                report.append(f"- **Phase {phase['phase']}: {phase['name']}** {status_emoji}")

                tasks = phase.get("tasks", [])
                if tasks and self.verbose:
                    for task in tasks:
                        report.append(f"  - {task}")

        # Goals
        goals = data.get("goals", [])
        if goals:
            report.append("")
            report.append("## Goals")
            for goal in goals:
                report.append(f"- {goal}")

        # Metrics
        metrics = data.get("success_metrics", [])
        if metrics:
            report.append("")
            report.append("## Success Metrics")
            for metric in metrics:
                report.append(f"- **{metric['metric']}**: {metric['target']} {metric['unit']}")

        return "\n".join(report)


@click.group()
def cli():
    """Sprint update agent for context system"""
    pass


@cli.command()
@click.option("--sprint", help="Specific sprint ID to update")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def update(sprint, verbose):
    """Update sprint document based on current state"""
    updater = SprintUpdater(sprint_id=sprint, verbose=verbose)
    updater.update_sprint()
    # Always exit with success - "no updates needed" is not a failure
    sys.exit(0)


@cli.command()
@click.option("--sprint", help="Specific sprint ID to report on")
@click.option("--verbose", is_flag=True, help="Include task details")
def report(sprint, verbose):
    """Generate sprint status report"""
    updater = SprintUpdater(sprint_id=sprint, verbose=verbose)
    print(updater.generate_report())


@cli.command()
@click.option("--label", help="GitHub label to watch")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def watch(label, verbose):
    """Watch for issue changes and update sprint (for CI/CD)"""
    updater = SprintUpdater(verbose=verbose)

    # This would be called by GitHub Actions on issue events
    success = updater.update_sprint()

    # Output for GitHub Actions
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::set-output name=updated::{str(success).lower()}")
        if updater.updates_made:
            updates_json = json.dumps(updater.updates_made)
            print(f"::set-output name=updates::{updates_json}")

    # Always exit with success - "no updates needed" is not a failure
    sys.exit(0)


if __name__ == "__main__":
    cli()
