#!/bin/bash
# Test script for Local CI PoC

echo "Testing Local CI Result Posting - Phase 1 PoC"
echo "============================================="
echo

# Test 1: Create mock CI results
echo "1. Creating mock CI results..."
cat > test-ci-results.json << 'EOF'
{
  "command": "all",
  "status": "PASSED",
  "target": "pipeline",
  "duration": "2m 15s",
  "checks": {
    "coverage": {
      "passed": true,
      "percentage": 87.5,
      "threshold": 85.0,
      "files_covered": 45,
      "lines_covered": 3250,
      "lines_total": 3714
    },
    "tests": {
      "passed": true,
      "total": 150,
      "passed_count": 148,
      "failed": 0,
      "skipped": 2,
      "duration": "45s"
    },
    "linting": {
      "passed": true,
      "issues": []
    }
  },
  "errors": [],
  "next_action": "All checks passed",
  "version": "1.0",
  "timestamp": "2025-07-23T12:00:00Z"
}
EOF
echo "✓ Mock results created"
echo

# Test 2: Test verification script
echo "2. Testing verify-ci-results.py..."
if python scripts/verify-ci-results.py test-ci-results.json; then
    echo "✓ Verification passed"
else
    echo "✗ Verification failed"
fi
echo

# Test 3: Test claude-ci.sh --output flag
echo "3. Testing claude-ci.sh output flag..."
# Just test the help and version commands to avoid running full CI
if ./scripts/claude-ci.sh check scripts/verify-ci-results.py --output test-output.json; then
    echo "✓ claude-ci output test passed"
    if [ -f test-output.json ]; then
        echo "✓ Output file created"
        # Show first few lines
        echo "Output preview:"
        head -5 test-output.json
    fi
else
    echo "✗ claude-ci test failed"
fi
echo

# Test 4: Show what posting would look like (dry run)
echo "4. Demonstrating post-ci-results.py (dry run)..."
echo "Would post results with:"
echo "  ./scripts/post-ci-results.py test-ci-results.json --pr 123"
echo

# Cleanup
rm -f test-ci-results.json test-output.json

echo "Phase 1 PoC testing complete!"
echo
echo "Next steps:"
echo "1. Create a test PR to fully demonstrate the workflow"
echo "2. Run: ./scripts/claude-ci.sh all --output results.json --post-results"
echo "3. The ci-local-verifier workflow will automatically verify the results"
