# Contributing

Guidelines for contributing: PR flow, reviewer matrix, coding standards.

- Branching: use pattern `type/scope-desc` (see rules)
- Never push directly to `main`.

## PR Flow

- Create feature branch from `main`.
- Submit PR with description.
- Code review required.
- CI must pass.

## Reviewer Matrix

- Code: Lead developer.
- Security: Security team.
- Design: UX designer.

## Coding Standards

- Follow PEP 8 for Python.
- Use TypeScript ESLint for JS/TS.
- 95% test coverage.

See `docs/CODING_STANDARDS.md` for detailed guidelines.

## Development Process

See `docs/SDLC.md` for the full Software Development Lifecycle.

## Testing

Testing strategy, CI requirements, unit/integration/e2e matrices.

### Strategy

- Unit tests: 95% code coverage for all modules.
- Integration tests: API endpoints, database interactions.
- E2E tests: Full user workflows, including voice and web interfaces.
- AI-specific tests: Bias detection, hallucination checks, memory accuracy.
- Performance tests: Load testing for 10k interactions.
- Security tests: Penetration testing, vulnerability scans.

### CI Requirements

- Automated builds on every PR.
- Run full test suite before merge.
- Code quality checks: Linting, static analysis.
- Deployment to staging on successful tests.

### Test Matrices

- Unit: Core functions (memory, agents).
- Integration: Service interactions.
- E2E: User scenarios (chat, task delegation).

## Definition of Done (DoD)

This document defines the criteria that must be met for an issue (feature, bug fix, or
task) to be considered "done" in the Kimberly project. The DoD ensures quality,
completeness, and alignment with project standards before marking issues as completed.

### Purpose

The Definition of Done provides a clear checklist to prevent incomplete work from being
accepted. It promotes consistency, reduces rework, and ensures that all aspects of
quality are addressed.

### Criteria

#### Code Quality

- [ ] Code follows [CODING_STANDARDS.md](CODING_STANDARDS.md) (e.g., PEP 8, type hints,
  documentation).
- [ ] Code is peer-reviewed via pull request with at least one approval.
- [ ] No linting errors or warnings (e.g., flake8, mypy).
- [ ] Code is modular, maintainable, and follows DRY principles.
- [ ] Sensitive data handling complies with
  [SECURE_CREDENTIALS_PLAN.md](SECURE_CREDENTIALS_PLAN.md).

#### Testing

- [ ] Unit tests written and passing (95% code coverage target).
- [ ] Integration tests for API endpoints and database interactions.
- [ ] E2E tests for user workflows (if applicable).
- [ ] AI-specific tests: Bias detection, hallucination checks, memory accuracy.
- [ ] Performance tests meet requirements (<1s latency, scalability).
- [ ] Security tests: Vulnerability scans, penetration testing.
- [ ] All tests pass in CI/CD pipeline.

#### Functionality

- [ ] Acceptance criteria from the issue are fully met.
- [ ] Feature works as expected in the development environment.
- [ ] No regressions introduced (existing functionality still works).
- [ ] Edge cases and error handling are addressed.
- [ ] Accessibility (WCAG 2.1) and usability requirements met.

#### Documentation

- [ ] Code is documented with docstrings and comments.
- [ ] API documentation updated (e.g., openapi.yaml).
- [ ] User-facing changes documented in README.md or relevant docs.
- [ ] Architecture changes documented in ARCHITECTURE.md or ADRs.

#### Security and Compliance

- [ ] Security review completed (threat modeling if needed).
- [ ] GDPR and privacy requirements met.
- [ ] No hardcoded secrets or credentials.
- [ ] Audit trails and logging implemented for relevant features.

#### Deployment and Operations

- [ ] Code deployed to staging environment successfully.
- [ ] Monitoring and alerting configured (e.g., Prometheus/Grafana).
- [ ] Backup and recovery procedures updated if applicable.
- [ ] Runbooks updated for operational changes.

#### Quality Assurance

- [ ] QA testing completed (manual or automated).
- [ ] No critical or high-severity bugs remaining.
- [ ] Performance benchmarks met.
- [ ] Cross-platform compatibility verified (if applicable).

### Exceptions

- For trivial tasks (e.g., typo fixes), some criteria may be waived with engineering
  lead approval.
- Prototypes or experimental features may have relaxed DoD until stabilized.

### Process

1. During sprint planning, ensure DoD is understood for each issue.
2. Before marking an issue as done, verify all criteria are checked.
3. If criteria cannot be met, discuss with engineering lead for adjustments.
4. Post-completion, issues are eligible for demo in sprint review.

### Review and Updates

This DoD will be reviewed quarterly or when project needs change. Updates require
agreement from the engineering lead and PM.

## Coding Standards

This document outlines the coding standards, best practices, and guidelines for the
Kimberly project. Adherence ensures consistency, maintainability, and quality across the
codebase.

### General Principles

- **Readability First**: Code should be self-documenting. Prioritize clarity over
  cleverness.
- **Consistency**: Follow established patterns in the codebase.
- **Security**: Validate inputs, avoid vulnerabilities (e.g., SQL injection, XSS).
- **Performance**: Write efficient code; profile when necessary.
- **Testing**: All code must be testable; aim for 95% coverage.
- **Documentation**: Document public APIs, complex logic, and decisions.

### Language-Specific Standards

#### Python

- **Style Guide**: Follow [PEP 8](https://pep8.org/) strictly.
  - Use 4 spaces for indentation (no tabs).
  - Line length: 88 characters (Black default).
  - Naming: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE`
    for constants.
- **Tools**:
  - Formatter: [Black](https://black.readthedocs.io/) for auto-formatting.
  - Linter: [Flake8](https://flake8.pycqa.org/) for style and errors.
  - Import Sorter: [isort](https://pycqa.github.io/isort/) for import organization.
  - Markdown linting: We use `markdownlint-cli2` in CI; local use requires Node >= 20.
    - To run locally:

      ```bash
      npx markdownlint-cli2 "**/*.md"
      # or use the helper script (prefers local npx)
      ./scripts/markdownlint.sh
      ```

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

#### JavaScript/TypeScript (if applicable)

- **Style Guide**: [Airbnb JavaScript Style
  Guide](https://github.com/airbnb/javascript).
- **Tools**: ESLint + Prettier.
- **Best Practices**: Use async/await, avoid callbacks; type everything in TS.

#### Other Languages

- Follow language-specific standards (e.g., Go: effective Go).

### Code Structure

- **Modular**: Small, focused functions/classes.
- **Separation of Concerns**: UI, business logic, data access layers.
- **DRY Principle**: No duplication; extract common code.
- **SOLID Principles**: Single responsibility, open/closed, etc.

### Version Control

- **Commits**: Clear, concise messages (e.g., "feat: add user auth endpoint").
- **Branches**: Feature branches from `main`; squash merges.
- **PRs**: Descriptive titles/descriptions; link issues.

### Testing

- **Unit Tests**: Test individual components.
- **Integration Tests**: Test interactions.
- **E2E Tests**: Full workflows.
- **Tools**: pytest for Python; Jest for JS.
- **Coverage**: 95% minimum; CI enforces.

### Documentation

- **Inline**: Comments for complex logic.
- **API Docs**: Use OpenAPI/Swagger.
- **Code Docs**: READMEs, docstrings.
- **Updates**: Keep docs current with code changes.

### CI/CD Integration

- All standards enforced via CI (linting, tests, coverage).
- PRs blocked if standards not met.

### Enforcement

- Code reviews check adherence.
- Automated tools flag violations.
- Training: New contributors review this doc.

For questions, see CONTRIBUTING.md or ask in discussions.
