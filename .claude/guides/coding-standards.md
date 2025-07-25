# Coding & Review Guidelines

## 📋 Language Style Guides

### JavaScript/TypeScript
- Follow Prettier defaults
- Use ESLint recommended rules
- Prefer `const` over `let`
- Use meaningful variable names

### Python
- Follow Black formatter
- Use type hints where appropriate
- Follow PEP 8 conventions
- Docstrings for all public functions

### General
- Clear, self-documenting code
- Comments for complex logic only
- Consistent naming conventions
- DRY (Don't Repeat Yourself)

## Testing Requirements
- Tests MUST accompany any new logic
- Aim for >80% code coverage
- Include unit and integration tests
- Use `/review` to verify test coverage

## Code Review Checklist
- [ ] Tests included and passing
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Documentation updated
- [ ] Performance considered
- [ ] Security implications reviewed

## Commit Standards
- Imperative mood: "Add feature" not "Added feature"
- Conventional Commits format
- Reference issues: "Fix #123"
- Keep commits atomic and focused

## Pull Request Guidelines
- Clear, descriptive title
- Detailed description of changes
- Screenshots for UI changes
- Test results included
- Link related issues
