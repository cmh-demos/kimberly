# Needs work — prioritized

This file lists the highest-priority documentation and project gaps I found, with short assessments and next actions.

## Top priority (fix now)
- README placeholders: add dev quickstart + runnable example (why: onboarding friction).  Next: add install, env, run steps and example `curl` and test data.
- `docs/openapi.yaml` dedupe & clean: remove duplicate schemas, complete error responses (why: client SDK generation breaks).  Next: run OpenAPI linter and add examples.

## High priority (this sprint)
- Sprint-plan: attach owners + measurable acceptance criteria (why: QA/ownership).  Next: turn into tickets with owners.
- Diagrams missing: add component and sequence Mermaid diagrams (why: clarify architecture & flows).  Next: embed sample mermaid diagrams in ARCHITECTURE.md.

## Medium priority
- CI checks for docs & APIs (openapi lint, doc build, copilot_tracking validation).  Next: add GitHub Actions or CI-agnostic pipeline.
- AI tests: memory accuracy, hallucination checks, bias detection (why: model QA).  Next: add testing matrix in TESTING.md.

## Lower priority / Nice to have
- Mobile plan: fill TBD in README with platform choices and distribution path.
- Add more examples & SDK snippets in `docs/API.md`.

## Notes and assessment
- Most gaps are documentation and validation gaps (fixes are straightforward). The openapi dedup + tests are most important to enable SDK and CI.

If you want, I can convert each top-priority item into tickets/PRs and start with README + OpenAPI cleanup.
