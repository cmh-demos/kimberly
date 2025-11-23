# Project Management — Board, Cadence & Metrics

This file consolidates project management materials: meeting cadence, reporting artifacts, KPIs, sprint plan mapping, and a simple project board. It replaces the previous `docs/PM_CADENCE_AND_METRICS.md`, `docs/PROJECT_BOARD.md`, `docs/NEEDS_WORK.md` and `docs/WIKI_HOME.md` to make the project management surface easier to find and maintain.

## Meetings & Cadences
- Weekly sync (30–45m) — core contributors: PM, Eng Lead, Backend, Frontend, SRE, Security. Purpose: sprint progress, blockers, decisions.
- Bi-weekly roadmap / backlog grooming (60m) — PM + leads: refine priorities and acceptance criteria.
- Sprint planning (start of each 2-week sprint) — plan sprint scope, owners, estimates.
- Sprint retro (end of sprint) — review what went well and improvements.
- Monthly stakeholder review (30–60m) — demo progress and review KPIs.

## Reporting artifacts
- Weekly status report (PRs merged, top blockers, next week plan) — short markdown note.
- Burndown chart per sprint (automated via project board) — track story completion vs estimated.
- Incident & risk log (high priority issues) — maintain a live doc for incidents.
- Release notes & changelog for each release.

## KPIs & Success Metrics
- Mean response latency — target <500ms local / <2s remote
- Memory relevance score — spot-check accuracy of memory recall
- Agent task success rate — percent tasks completed successfully with no escalation
- Error/exception rate — API error rate target <1%
- Telemetry coverage — percent flows instrumented, target 95%
- Closed beta retention — N-week retention for beta users
- CI/Test coverage — aim >=80% for MVP; 95% target for core services

## Project Board (lightweight)
### Backlog (sample)
- **Epic A — Developer onboarding & CI**
  - Story A.1: Create a runnable Quickstart + example (README + test harness).
  - Story A.2: Add CI checks: openapi linter, docs build, copilot_tracking schema validation.
  - Story A.3: Clean `docs/openapi.yaml` duplicates and add examples.
- **Epic B — Core chat pipeline & short-term memory**
  - Story B.1: Implement POST /chat end-to-end with basic TTS/ASR mocked.
  - Story B.2: Short-term memory API (add/list/delete) with canonical quotas.
  - Story B.3: E2E smoke tests and memory recall tests.
- **Epic C — Long-term memory, meditation, and pruning**
  - Story C.1: Memory ranking and nightly "meditation" rotation.
  - Story C.2: Long-term persistence and retention/migration tests.
- **Epic D — Agent skeleton & safety**
  - Story D.1: Agent runner prototype with quotas.
  - Story D.2: Sandboxing + failure handling + quotas enforcement.

## Sprint mapping (example)
- Sprint 1: A.1, B.1, B.2
- Sprint 2: A.2, A.3, B.3, C.1
- Sprint 3: C.2, D.1, D.2

## Needs work / backlog highlights
Lots of existing items live here; this consolidated file duplicates and centralizes the highest priority docs so the board and cadence live together with action items and top open gaps.

## Next Steps
- Convert top backlog items into issues and assign owners.
- Link this file from `README.md` and release notes.
