# Test Coverage Improvement Plan

## Current Status (as of 2025-07-12)

- **Line Coverage**: 49.05% (target: 50%)
- **Branch Coverage**: 36.21% (target: 35%)
- **Mutation Score**: 75.00% (target: 75%)
- **Critical Functions**: 100.00% (target: 100%) ✅

## Priority Files for Coverage Improvement

### High Priority (0-40% coverage)
1. **hash_diff_embedder_async.py** - 0.00% coverage (166 lines)
   - Completely untested async embedder
   - Create comprehensive async test suite

2. **neo4j_init.py** - 31.27% coverage (127 missing lines)
   - Missing database connection tests
   - Add constraint and index creation tests

3. **sum_scores_api.py** - 32.84% coverage (125 missing lines)
   - API endpoint testing needed
   - Add error handling tests

4. **kv_validators.py** - 33.64% coverage (45 missing lines)
   - Validation logic needs tests
   - Add edge case tests

5. **config_validator.py** - 34.66% coverage (93 missing lines)
   - Configuration validation tests needed
   - Add schema validation tests

6. **context_analytics.py** - 35.62% coverage (160 missing lines)
   - Analytics functionality needs tests
   - Add metric calculation tests

7. **vector_db_init.py** - 36.14% coverage (76 missing lines)
   - Vector database setup tests needed
   - Add connection and collection tests

### Medium Priority (40-60% coverage)
8. **context_lint.py** - 45.05% coverage (117 missing lines)
9. **graph_builder.py** - 48.59% coverage (126 missing lines)
10. **hash_diff_embedder.py** - 51.37% coverage (87 missing lines)
11. **graphrag_integration.py** - 52.66% coverage (112 missing lines)
12. **context_kv.py** - 55.91% coverage (189 missing lines)

### Good Coverage (70%+)
13. **sprint_issue_linker.py** - 71.69% coverage ✅
14. **base_component.py** - 72.48% coverage ✅
15. **cleanup_agent.py** - 73.78% coverage ✅
16. **update_sprint.py** - 77.66% coverage ✅
17. **utils.py** - 88.89% coverage ✅

## Improvement Strategy

### Phase 1: Fix Critical Gaps (Target: 60% line coverage)
- [ ] Add async embedder tests
- [ ] Add Neo4j initialization tests
- [ ] Add API endpoint tests
- [ ] Add validator tests

### Phase 2: Strengthen Core Modules (Target: 70% line coverage)
- [ ] Improve graph builder tests
- [ ] Add comprehensive KV store tests
- [ ] Enhance integration tests

### Phase 3: Excellence (Target: 85% line coverage)
- [ ] Add edge case tests
- [ ] Improve error handling coverage
- [ ] Add performance tests
- [ ] Increase branch coverage

## Incremental Targets

| Milestone | Line Coverage | Branch Coverage | Timeline |
|-----------|---------------|-----------------|----------|
| Current   | 49%          | 36%             | ✅ Done  |
| Phase 1   | 60%          | 45%             | Week 1   |
| Phase 2   | 70%          | 55%             | Week 2   |
| Phase 3   | 85%          | 70%             | Week 4   |

## Test Quality Standards

- All new tests must include:
  - Happy path scenarios
  - Error conditions
  - Edge cases
  - Mock external dependencies
  - Clear assertions

- Branch coverage requirements:
  - Test both if/else branches
  - Test exception handling
  - Test different configuration paths

- Mutation testing improvements:
  - Strong assertions that catch value changes
  - Test boundary conditions
  - Avoid trivial assertions
