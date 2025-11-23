# Coding Standards

This document outlines the coding standards, best practices, and guidelines for the Kimberly project. Adherence ensures consistency, maintainability, and quality across the codebase.

## General Principles
- **Readability First**: Code should be self-documenting. Prioritize clarity over cleverness.
- **Consistency**: Follow established patterns in the codebase.
- **Security**: Validate inputs, avoid vulnerabilities (e.g., SQL injection, XSS).
- **Performance**: Write efficient code; profile when necessary.
- **Testing**: All code must be testable; aim for 95% coverage.
- **Documentation**: Document public APIs, complex logic, and decisions.

## Language-Specific Standards

### Python
- **Style Guide**: Follow [PEP 8](https://pep8.org/) strictly.
  - Use 4 spaces for indentation (no tabs).
  - Line length: 88 characters (Black default).
  - Naming: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants.
- **Tools**:
  - Formatter: [Black](https://black.readthedocs.io/) for auto-formatting.
  - Linter: [Flake8](https://flake8.pycqa.org/) for style and errors.
  - Import Sorter: [isort](https://pycqa.github.io/isort/) for import organization.
- **Best Practices**:
  - Use type hints (mypy for checking).
  - Avoid global variables; use dependency injection.
  - Handle exceptions properly; log errors.
  - Use context managers for resources (e.g., files, DB connections).
  - Prefer list/dict comprehensions for readability.
  - Document with docstrings (Google/NumPy style).
- **Security**:
  - Sanitize inputs; use parameterized queries for DB.
  - Avoid `eval()` or `exec()`.
  - Use `secrets` module for random values.

### JavaScript/TypeScript (if applicable)
- **Style Guide**: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- **Tools**: ESLint + Prettier.
- **Best Practices**: Use async/await, avoid callbacks; type everything in TS.

### Other Languages
- Follow language-specific standards (e.g., Go: effective Go).

## Code Structure
- **Modular**: Small, focused functions/classes.
- **Separation of Concerns**: UI, business logic, data access layers.
- **DRY Principle**: No duplication; extract common code.
- **SOLID Principles**: Single responsibility, open/closed, etc.

## Version Control
- **Commits**: Clear, concise messages (e.g., "feat: add user auth endpoint").
- **Branches**: Feature branches from `main`; squash merges.
- **PRs**: Descriptive titles/descriptions; link issues.

## Testing
- **Unit Tests**: Test individual components.
- **Integration Tests**: Test interactions.
- **E2E Tests**: Full workflows.
- **Tools**: pytest for Python; Jest for JS.
- **Coverage**: 95% minimum; CI enforces.

## Documentation
- **Inline**: Comments for complex logic.
- **API Docs**: Use OpenAPI/Swagger.
- **Code Docs**: READMEs, docstrings.
- **Updates**: Keep docs current with code changes.

## CI/CD Integration
- All standards enforced via CI (linting, tests, coverage).
- PRs blocked if standards not met.

## Enforcement
- Code reviews check adherence.
- Automated tools flag violations.
- Training: New contributors review this doc.

For questions, see CONTRIBUTING.md or ask in discussions.