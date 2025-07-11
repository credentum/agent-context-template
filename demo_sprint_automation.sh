#!/bin/bash
# Demo script for sprint automation features

echo "=== Sprint Automation Demo ==="
echo

echo "1. Current Sprint Status:"
python update_sprint.py report --verbose
echo

echo "2. Validating Sprint Document:"
python context_lint.py validate context/sprints/sprint-001.yaml --verbose
echo

echo "3. Sprint Update Simulation (dry run):"
echo "   This would update sprint status based on GitHub issues"
echo "   python update_sprint.py update --verbose"
echo

echo "4. Issue Creation Simulation (dry run):"
python sprint_issue_linker.py create --dry-run --verbose
echo

echo "5. Available Commands:"
echo "   - Start sprint: create label 'start-sprint-N' or use GitHub Actions"
echo "   - Update sprint: python update_sprint.py update"
echo "   - Generate report: python update_sprint.py report"
echo "   - Create issues: python sprint_issue_linker.py create"
echo

echo "=== Demo Complete ==="