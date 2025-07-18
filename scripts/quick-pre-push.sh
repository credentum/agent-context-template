#!/bin/bash
# quick-pre-push.sh - Fast pre-push validation (essential checks only)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Quick Pre-Push Validation${NC}"
echo -e "${YELLOW}Running essential checks only...${NC}"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    exit 1
fi

# Quick Python syntax check
echo -e "${BLUE}🔍 Checking Python syntax...${NC}"
python -m py_compile src/**/*.py tests/**/*.py 2>/dev/null || {
    echo -e "${RED}❌ Python syntax errors found${NC}"
    exit 1
}

# Quick import check
echo -e "${BLUE}🔍 Checking critical imports...${NC}"
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.validators.config_validator import ConfigValidator
    from src.validators.kv_validators import validate_cache_entry
    import jsonschema
    print('✅ Critical imports working')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
" || exit 1

# Quick YAML validation (skip schema files)
echo -e "${BLUE}🔍 Checking YAML syntax...${NC}"
python -c "
import yaml
import os
try:
    for root, dirs, files in os.walk('context'):
        # Skip schema directory - uses yamale format
        if 'schemas' in root:
            continue
        for file in files:
            if file.endswith('.yaml') or file.endswith('.yml'):
                with open(os.path.join(root, file)) as f:
                    yaml.safe_load(f)
    print('✅ YAML syntax valid')
except Exception as e:
    print(f'❌ YAML syntax error: {e}')
    exit(1)
" || exit 1

# Quick workflow YAML check
echo -e "${BLUE}🔍 Checking workflow YAML syntax...${NC}"
python -c "
import yaml
import os
try:
    for root, dirs, files in os.walk('.github/workflows'):
        for file in files:
            if file.endswith('.yml'):
                with open(os.path.join(root, file)) as f:
                    yaml.safe_load(f)
    print('✅ Workflow YAML syntax valid')
except Exception as e:
    print(f'❌ Workflow YAML syntax error: {e}')
    exit(1)
" || exit 1

echo -e "${GREEN}✅ Quick pre-push validation passed!${NC}"
echo -e "${YELLOW}💡 For full validation, run: ./scripts/run-ci-docker.sh${NC}"
