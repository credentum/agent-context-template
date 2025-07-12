#!/bin/bash
# Script to run comprehensive test coverage

echo "🔍 Running comprehensive test coverage analysis..."
echo "================================================"

# Clean previous coverage data
rm -f .coverage
rm -rf htmlcov/
rm -f coverage.xml coverage.json

# Run tests with coverage
echo "📊 Running tests with branch coverage..."
python -m pytest \
    --cov=src \
    --cov-branch \
    --cov-report=term-missing:skip-covered \
    --cov-report=html \
    --cov-report=xml \
    --cov-report=json \
    -v

# Check if tests passed
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Fix failing tests before checking coverage."
    exit 1
fi

# Parse coverage results
echo ""
echo "📈 Coverage Summary:"
echo "==================="
python -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
    total = data['totals']
    print(f'Line Coverage: {total[\"percent_covered\"]:.2f}%')
    print(f'Branch Coverage: {total.get(\"percent_branch_covered\", 0):.2f}%')
    print(f'Missing Lines: {total[\"missing_lines\"]}')
    print(f'Missing Branches: {total.get(\"missing_branches\", 0)}')
"

# Generate coverage badge (optional)
if command -v coverage-badge &> /dev/null; then
    echo ""
    echo "🏷️  Generating coverage badge..."
    coverage-badge -o coverage.svg -f
fi

# Check coverage thresholds
echo ""
echo "🎯 Checking coverage thresholds..."
python -c "
import json
import sys

with open('coverage.json') as f:
    data = json.load(f)
    total = data['totals']
    
    line_coverage = total['percent_covered']
    branch_coverage = total.get('percent_branch_covered', 0)
    
    targets = {
        'Line Coverage': (line_coverage, 85),
        'Branch Coverage': (branch_coverage, 70)
    }
    
    all_passed = True
    for metric, (actual, target) in targets.items():
        status = '✅' if actual >= target else '❌'
        print(f'{status} {metric}: {actual:.2f}% (target: ≥{target}%)')
        if actual < target:
            all_passed = False
    
    if not all_passed:
        print('\n⚠️  Coverage targets not met!')
        sys.exit(1)
    else:
        print('\n✅ All coverage targets met!')
"

echo ""
echo "📄 Coverage reports generated:"
echo "  - Terminal: See output above"
echo "  - HTML: htmlcov/index.html"
echo "  - XML: coverage.xml"
echo "  - JSON: coverage.json"