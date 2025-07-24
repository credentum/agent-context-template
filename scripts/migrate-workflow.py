#!/usr/bin/env python3
"""
Workflow Migration Tool for CI Migration Phase 3
Converts GitHub Actions workflows to use the verifier pattern
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class WorkflowMigrator:
    """Converts GitHub Actions workflows to verifier pattern"""

    def __init__(self, workflows_dir: str = ".github/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.backup_dir = self.workflows_dir / "backup"
        self.verifier_job_template = {
            "verify-ci-results": {
                "name": "Verify Local CI Results",
                "runs-on": "ubuntu-latest",
                "if": "github.event_name == 'pull_request'",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v4"},
                    {
                        "name": "Verify CI Results",
                        "uses": "./.github/actions/verify-ci-results",
                        "with": {"mode": "${{ env.CI_MIGRATION_MODE || 'parallel' }}"},
                    },
                ],
            }
        }

    def backup_workflow(self, workflow_path: Path) -> Path:
        """Create backup of original workflow"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{workflow_path.stem}.backup.{timestamp}.yml"

        self.backup_dir.mkdir(exist_ok=True)
        shutil.copy2(workflow_path, backup_path)

        return backup_path

    def parse_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """Parse YAML workflow file"""
        with open(workflow_path, "r") as f:
            return yaml.safe_load(f)

    def identify_ci_jobs(self, workflow: Dict[str, Any]) -> List[str]:
        """Identify jobs that are CI-related"""
        ci_keywords = ["test", "lint", "check", "validate", "coverage", "type", "format"]
        ci_jobs = []

        jobs = workflow.get("jobs", {})
        for job_name, job_config in jobs.items():
            # Check job name
            if any(keyword in job_name.lower() for keyword in ci_keywords):
                ci_jobs.append(job_name)
                continue

            # Check job steps
            steps = job_config.get("steps", [])
            for step in steps:
                if isinstance(step, dict):
                    step_name = step.get("name", "").lower()
                    if any(keyword in step_name for keyword in ci_keywords):
                        ci_jobs.append(job_name)
                        break

        return list(set(ci_jobs))

    def add_verifier_pattern(self, workflow: Dict[str, Any], ci_jobs: List[str]) -> Dict[str, Any]:
        """Add verifier pattern to workflow"""
        # Add CI migration mode environment variable
        if "env" not in workflow:
            workflow["env"] = {}

        workflow["env"]["CI_MIGRATION_MODE"] = "${{ vars.CI_MIGRATION_MODE || 'parallel' }}"

        # Add verifier job
        if "jobs" not in workflow:
            workflow["jobs"] = {}

        workflow["jobs"].update(self.verifier_job_template)

        # Make CI jobs conditional based on migration mode
        for job_name in ci_jobs:
            if job_name in workflow["jobs"]:
                job = workflow["jobs"][job_name]

                # Add condition to skip in verifier-only mode
                existing_if = job.get("if", "true")
                new_condition = f"({existing_if}) && (env.CI_MIGRATION_MODE != 'verifier-only')"
                job["if"] = new_condition

        # Update job dependencies
        verifier_job = workflow["jobs"]["verify-ci-results"]
        verifier_job["needs"] = ci_jobs
        verifier_job["if"] = "always() && github.event_name == 'pull_request'"

        return workflow

    def create_parallel_monitoring(self, workflow_name: str, ci_jobs: List[str]) -> Dict[str, Any]:
        """Create monitoring configuration for parallel execution"""
        return {
            "workflow": workflow_name,
            "ci_jobs": ci_jobs,
            "monitoring": {
                "compare_results": True,
                "track_performance": True,
                "alert_on_mismatch": True,
            },
        }

    def migrate_workflow(self, workflow_path: Path, dry_run: bool = False) -> Optional[Path]:
        """Migrate a single workflow file"""
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {workflow_path.name}...")

        # Parse workflow
        try:
            workflow = self.parse_workflow(workflow_path)
        except Exception as e:
            print(f"  ❌ Failed to parse: {e}")
            return None

        # Check if already migrated
        if "verify-ci-results" in workflow.get("jobs", {}):
            print("  ⏭️  Already migrated, skipping")
            return None

        # Identify CI jobs
        ci_jobs = self.identify_ci_jobs(workflow)
        if not ci_jobs:
            print("  ⏭️  No CI jobs found, skipping")
            return None

        print(f"  📋 Found CI jobs: {', '.join(ci_jobs)}")

        if not dry_run:
            # Backup original
            backup_path = self.backup_workflow(workflow_path)
            print(f"  💾 Backed up to: {backup_path.name}")

            # Add verifier pattern
            migrated_workflow = self.add_verifier_pattern(workflow, ci_jobs)

            # Write updated workflow
            with open(workflow_path, "w") as f:
                yaml.dump(migrated_workflow, f, sort_keys=False, default_flow_style=False)

            print("  ✅ Migrated successfully")

            # Create monitoring config
            monitoring_config = self.create_parallel_monitoring(workflow_path.stem, ci_jobs)
            monitoring_path = self.workflows_dir / f".{workflow_path.stem}.monitoring.json"

            with open(monitoring_path, "w") as f:
                json.dump(monitoring_config, f, indent=2)

            print(f"  📊 Created monitoring config: {monitoring_path.name}")

            return workflow_path
        else:
            print("  ✨ Would migrate with verifier pattern")
            return None

    def migrate_all(
        self, target_workflows: Optional[List[str]] = None, dry_run: bool = False
    ) -> List[Path]:
        """Migrate all or specified workflows"""
        migrated = []

        # Get workflow files
        workflow_files = list(self.workflows_dir.glob("*.yml")) + list(
            self.workflows_dir.glob("*.yaml")
        )

        # Filter if specific workflows requested
        if target_workflows:
            workflow_files = [f for f in workflow_files if f.stem in target_workflows]

        print(f"\nFound {len(workflow_files)} workflow(s) to process")

        for workflow_file in workflow_files:
            result = self.migrate_workflow(workflow_file, dry_run)
            if result:
                migrated.append(result)

        return migrated

    def create_verifier_action(self) -> None:
        """Create the verify-ci-results composite action"""
        action_dir = Path(".github/actions/verify-ci-results")
        action_dir.mkdir(parents=True, exist_ok=True)

        action_yaml = {
            "name": "Verify CI Results",
            "description": "Verify local CI results in GitHub Actions",
            "inputs": {
                "mode": {
                    "description": "Verification mode: parallel, verifier-only, or traditional",
                    "required": False,
                    "default": "parallel",
                }
            },
            "runs": {
                "using": "composite",
                "steps": [
                    {
                        "name": "Verify Results",
                        "shell": "bash",
                        "run": """
if [ "${{ inputs.mode }}" = "traditional" ]; then
  echo "Running in traditional mode - skipping verification"
  exit 0
fi

echo "🔍 Verifying CI results (mode: ${{ inputs.mode }})"

# Check for CI results artifact
if [ ! -f "ci-results.json.gpg" ]; then
  echo "❌ No CI results found - push must run local CI first"
  exit 1
fi

# Verify GPG signature
python scripts/verify-ci-results.py --file ci-results.json.gpg || exit 1

# In parallel mode, also run GitHub CI for comparison
if [ "${{ inputs.mode }}" = "parallel" ]; then
  echo "Running GitHub CI for comparison..."
  # This would normally trigger the actual CI jobs
fi
""",
                    }
                ],
            },
        }

        action_file = action_dir / "action.yml"
        with open(action_file, "w") as f:
            yaml.dump(action_yaml, f, sort_keys=False, default_flow_style=False)

        print(f"\n✅ Created verifier action at {action_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate GitHub Actions workflows to verifier pattern"
    )
    parser.add_argument(
        "--workflows", nargs="+", help="Specific workflows to migrate (without extension)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--create-action", action="store_true", help="Create the verify-ci-results composite action"
    )
    parser.add_argument(
        "--workflows-dir", default=".github/workflows", help="Path to workflows directory"
    )

    args = parser.parse_args()

    # Change to repository root
    repo_root = os.environ.get("GITHUB_WORKSPACE", ".")
    os.chdir(repo_root)

    migrator = WorkflowMigrator(args.workflows_dir)

    # Create verifier action if requested
    if args.create_action:
        migrator.create_verifier_action()
        return

    # Priority workflows for migration
    priority_workflows = [
        "test",
        "lint-verification",
        "test-coverage",
        "ci-unified",
        "claude-code-review",
        "context-lint",
    ]

    target_workflows = args.workflows or priority_workflows

    print(f"{'DRY RUN MODE' if args.dry_run else 'MIGRATION MODE'}")
    print(f"Target workflows: {', '.join(target_workflows)}")

    # Perform migration
    migrated = migrator.migrate_all(target_workflows, args.dry_run)

    print(f"\n{'Would migrate' if args.dry_run else 'Migrated'} {len(migrated)} workflow(s)")

    if not args.dry_run and migrated:
        print("\n📝 Next steps:")
        print("1. Review the migrated workflows")
        print("2. Commit changes to a feature branch")
        print("3. Test in parallel mode (CI_MIGRATION_MODE=parallel)")
        print("4. Monitor results with scripts/monitor-ci-migration.sh")
        print("5. Gradually switch to verifier-only mode")


if __name__ == "__main__":
    main()
