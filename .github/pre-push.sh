#\!/bin/bash
# Pre-push hook to run tests before pushing

echo "🧪 Running tests before push..."

# Run the same tests that CI runs
echo "Running unit tests..."
python -m pytest tests/ -v --tb=short -m "not integration and not e2e" \
  --cov=. --cov-report=term-missing --cov-report=xml \
  --timeout=60 --timeout-method=thread -x

if [ $? -ne 0 ]; then
    echo "❌ Tests failed\! Push aborted."
    exit 1
fi

echo "✅ All tests passed\! Proceeding with push..."
