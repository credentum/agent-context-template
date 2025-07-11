#!/usr/bin/env python3
"""
Cleanup Agent for the Agent-First Context System

This agent automatically archives expired documents and maintains
the health of the context system by:
- Moving expired documents to context/archive/
- Cleaning up old logs
- Updating cleanup.yaml with actions taken
"""

import os
import shutil
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import click


class CleanupAgent:
    """Agent responsible for context system maintenance"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.context_dir = Path("context")
        self.archive_dir = self.context_dir / "archive"
        self.cleanup_log_path = self.context_dir / "logs" / "cleanup.yaml"
        self.actions: List[Dict[str, Any]] = []
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(".ctxrc.yaml", 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            if self.verbose:
                click.echo(f"Warning: Could not load .ctxrc.yaml: {e}")
            # Return default config
            return {
                'storage': {'retention_days': 90},
                'agents': {'cleanup': {'expire_after_days': 30}}
            }
    
    def _log_action(self, action: str, file_path: Path, reason: str) -> None:
        """Log an action taken by the cleanup agent"""
        self.actions.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'file': str(file_path),
            'reason': reason
        })
        
        if self.verbose:
            click.echo(f"{action}: {file_path} - {reason}")
    
    def _should_archive(self, file_path: Path, data: Dict[str, Any]) -> tuple[bool, str]:
        """Determine if a document should be archived"""
        # Check if expired
        expires = data.get('expires')
        if expires:
            expire_date = datetime.strptime(expires, '%Y-%m-%d')
            if expire_date < datetime.now():
                return True, f"Document expired on {expires}"
        
        # Check if deprecated and old
        if data.get('status') == 'deprecated':
            last_modified = data.get('last_modified')
            if last_modified:
                mod_date = datetime.strptime(last_modified, '%Y-%m-%d')
                days_old = (datetime.now() - mod_date).days
                threshold = self.config['agents']['cleanup']['expire_after_days']
                if days_old > threshold:
                    return True, f"Deprecated document not modified for {days_old} days"
        
        # Check retention policy
        last_referenced = data.get('last_referenced')
        if last_referenced:
            ref_date = datetime.strptime(last_referenced, '%Y-%m-%d')
            days_since_ref = (datetime.now() - ref_date).days
            retention_days = self.config['storage']['retention_days']
            if days_since_ref > retention_days:
                return True, f"Document not referenced for {days_since_ref} days (retention: {retention_days})"
        
        return False, ""
    
    def archive_document(self, file_path: Path) -> bool:
        """Archive a single document"""
        try:
            # Create archive subdirectory based on date
            archive_subdir = self.archive_dir / datetime.now().strftime('%Y-%m')
            archive_subdir.mkdir(parents=True, exist_ok=True)
            
            # Determine archive path
            archive_path = archive_subdir / file_path.name
            
            # Handle duplicates
            if archive_path.exists():
                base = archive_path.stem
                ext = archive_path.suffix
                counter = 1
                while archive_path.exists():
                    archive_path = archive_subdir / f"{base}_{counter}{ext}"
                    counter += 1
            
            # Move file
            if not self.dry_run:
                shutil.move(str(file_path), str(archive_path))
            
            self._log_action("ARCHIVED", file_path, f"Moved to {archive_path}")
            return True
            
        except Exception as e:
            self._log_action("ERROR", file_path, f"Failed to archive: {e}")
            return False
    
    def clean_logs(self) -> None:
        """Clean up old log files"""
        logs_dir = self.context_dir / "logs"
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for log_subdir in logs_dir.iterdir():
            if not log_subdir.is_dir() or log_subdir.name == "cleanup":
                continue
            
            # Check prompts directory with date structure
            if log_subdir.name == "prompts":
                for date_dir in log_subdir.iterdir():
                    if date_dir.is_dir():
                        try:
                            dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                            if dir_date < cutoff_date:
                                if not self.dry_run:
                                    shutil.rmtree(date_dir)
                                self._log_action("CLEANED", date_dir, f"Old prompts directory")
                        except ValueError:
                            continue
    
    def process_context_files(self) -> None:
        """Process all context files for cleanup"""
        # Skip certain directories
        skip_dirs = {'archive', 'schemas', 'logs', 'mcp_contracts'}
        
        for yaml_file in self.context_dir.rglob("*.yaml"):
            # Skip files in excluded directories
            if any(skip_dir in yaml_file.parts for skip_dir in skip_dirs):
                continue
            
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                
                if not data:
                    continue
                
                should_archive, reason = self._should_archive(yaml_file, data)
                if should_archive:
                    self.archive_document(yaml_file)
                    
            except Exception as e:
                self._log_action("ERROR", yaml_file, f"Failed to process: {e}")
    
    def write_cleanup_log(self) -> None:
        """Write cleanup actions to log file"""
        if not self.actions:
            return
        
        # Load existing log or create new
        log_data = {'cleanup_runs': []}
        if self.cleanup_log_path.exists() and not self.dry_run:
            try:
                with open(self.cleanup_log_path, 'r') as f:
                    log_data = yaml.safe_load(f) or {'cleanup_runs': []}
            except Exception:
                pass
        
        # Add this run
        run_data = {
            'run_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'timestamp': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'actions_count': len(self.actions),
            'actions': self.actions
        }
        
        log_data['cleanup_runs'].append(run_data)
        
        # Keep only last 100 runs
        log_data['cleanup_runs'] = log_data['cleanup_runs'][-100:]
        
        # Write log
        if not self.dry_run:
            self.cleanup_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cleanup_log_path, 'w') as f:
                yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    def run(self) -> None:
        """Execute cleanup tasks"""
        click.echo("Starting cleanup agent...")
        if self.dry_run:
            click.echo("(DRY RUN - no changes will be made)")
        
        # Process context files
        self.process_context_files()
        
        # Clean old logs
        self.clean_logs()
        
        # Write cleanup log
        self.write_cleanup_log()
        
        # Summary
        click.echo(f"\nCleanup complete:")
        click.echo(f"  Total actions: {len(self.actions)}")
        
        action_counts = {}
        for action in self.actions:
            action_type = action['action']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        for action_type, count in sorted(action_counts.items()):
            click.echo(f"  {action_type}: {count}")


@click.command()
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def main(dry_run, verbose):
    """Run the cleanup agent for context system maintenance"""
    agent = CleanupAgent(dry_run=dry_run, verbose=verbose)
    agent.run()


if __name__ == '__main__':
    main()