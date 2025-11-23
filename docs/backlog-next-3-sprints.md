# Prioritized Backlog — next 3 sprints (6 weeks)

This backlog converts audit findings into epics and prioritized user stories for the next three sprints (Sprint 1–3 in the 3-month plan). Owners and rough estimates are suggested; we can convert these into GitHub issues next.

## Epic A — Developer onboarding & CI (High priority)
- Story A.1: Create a runnable Quickstart + example (README + test harness). — owner: Docs/FE, estimate: 2 days
- Story A.2: Add CI checks: openapi linter, docs build, copilot_tracking schema validation. — owner: SRE, estimate: 3 days
- Story A.3: Clean `docs/openapi.yaml` duplicates and add examples. — owner: Backend, estimate: 3–5 days

## Epic B — Core chat pipeline & short-term memory (Highest priority)
- Story B.1: Implement POST /chat end-to-end with basic TTS/ASR mocked. — owner: Backend/FE, estimate: 5 days
-- Story B.2: Short-term memory API (add/list/delete) with canonical quotas (see `docs/memory-model.md`) — owner: Backend, estimate: 4 days
- Story B.3: E2E smoke tests and memory recall tests. — owner: QA, estimate: 3 days

## Epic C — Long-term memory, meditation, and pruning (High)
- Story C.1: Memory ranking and nightly "meditation" rotation. — owner: Backend, estimate: 6 days
-- Story C.2: Long-term persistence (canonical quotas — see `docs/memory-model.md`) and retention/migration tests. — owner: Backend, estimate: 4 days

## Epic D — Agent skeleton & safety (Medium)
- Story D.1: Agent runner prototype with quotas (Scheduler, Researcher) — owner: Backend, estimate: 5 days
- Story D.2: Sandboxing + failure handling + quotas enforcement — owner: SRE/Security, estimate: 4 days

## Sprint plan mapping (6-week view)
- Sprint 1: A.1, B.1, B.2 (quickstart, chat API, short-term memory)
- Sprint 2: A.2, A.3, B.3, C.1 (CI checks, openapi, tests, meditation prototype)
- Sprint 3: C.2, D.1, D.2 (long-term memory hardening, agents skeleton, sandboxing)

## Next steps I can take (select 1):
- Create GitHub issues for each story with labels and owners.
- Open PRs for Quickstart README + CI changes.
- Break down stories into sub-tasks and acceptance criteria.
