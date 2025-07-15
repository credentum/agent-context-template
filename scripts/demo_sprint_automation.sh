#!/bin/bash
# Demo script for sprint automation features

echo "=== Sprint Automation Demo ==="
echo

echo "1. Current Sprint Status:"
python -m src.agents.update_sprint report --verbose
echo

echo "2. Validating Sprint Document:"
python -m src.agents.context_lint validate context/sprints/sprint-001.yaml --verbose
echo

echo "3. Sprint Update Simulation (dry run):"
echo "   This would update sprint status based on GitHub issues"
echo "   python -m src.agents.update_sprint update --verbose"
echo

echo "4. Issue Creation Simulation (dry run):"
python -m src.agents.sprint_issue_linker create --dry-run --verbose
echo

echo "5. Available Commands:"
echo "   - Start sprint: create label 'start-sprint-N' or use GitHub Actions"
echo "   - Update sprint: python -m src.agents.update_sprint update"
echo "   - Generate report: python -m src.agents.update_sprint report"
echo "   - Create issues: python -m src.agents.sprint_issue_linker create"
echo

echo "=== Demo Complete ==="
