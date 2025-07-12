#!/bin/bash
# Script to run mutation testing for critical functions

echo "🧬 Running Mutation Testing..."
echo "=============================="

# Check if mutmut is installed
if ! command -v mutmut &> /dev/null; then
    echo "❌ mutmut not found. Installing..."
    pip install mutmut
fi

# Clean previous results
rm -f .mutmut-cache

# Run mutation testing on critical modules
echo "🎯 Testing critical modules..."

# Define critical modules to test
CRITICAL_MODULES=(
    "src/agents/cleanup_agent.py"
    "src/agents/update_sprint.py"
    "src/storage/context_kv.py"
    "src/storage/graph_builder.py"
    "src/validators/config_validator.py"
    "src/validators/kv_validators.py"
)

# Run mutmut on each critical module
for module in "${CRITICAL_MODULES[@]}"; do
    echo ""
    echo "📝 Mutating: $module"
    echo "------------------------"
    
    # Run mutation testing
    mutmut run --paths-to-mutate="$module" --runner="python -m pytest -x -q tests/" || true
    
    # Show results
    echo "Results for $module:"
    mutmut show
done

# Generate HTML report
echo ""
echo "📊 Generating mutation report..."
mutmut html

# Calculate mutation score
echo ""
echo "📈 Mutation Testing Summary:"
echo "============================"
mutmut results

# Parse and check mutation score
python -c "
import subprocess
import re

result = subprocess.run(['mutmut', 'results'], capture_output=True, text=True)
output = result.stdout

# Extract mutation statistics
total_match = re.search(r'Total: (\d+)', output)
killed_match = re.search(r'Killed: (\d+)', output)
survived_match = re.search(r'Survived: (\d+)', output)

if total_match and killed_match:
    total = int(total_match.group(1))
    killed = int(killed_match.group(1))
    survived = int(survived_match.group(1)) if survived_match else 0
    
    if total > 0:
        mutation_score = (killed / total) * 100
        print(f'')
        print(f'Mutation Score: {mutation_score:.2f}%')
        print(f'Killed: {killed}/{total}')
        print(f'Survived: {survived}')
        
        if mutation_score >= 80:
            print(f'✅ Mutation score target met (≥80%)')
        else:
            print(f'❌ Mutation score below target (<80%)')
    else:
        print('No mutations generated')
"

echo ""
echo "📄 Reports generated:"
echo "  - HTML: html/index.html"
echo "  - Use 'mutmut show <id>' to see specific mutations"