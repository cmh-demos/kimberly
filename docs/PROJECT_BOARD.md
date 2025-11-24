# Kimberly Project Board

This is a simple project board representation using Markdown. Use this to track progress
on epics and stories from the backlog.

## Backlog

- [ ] **Epic A — Developer onboarding & CI**
  - [ ] Story A.1: Create a runnable Quickstart + example (README + test harness). —
    owner: Docs/FE, estimate: 2 days
  - [ ] Story A.2: Add CI checks: openapi linter, docs build, copilot_tracking schema
    validation. — owner: SRE, estimate: 3 days
  - [ ] Story A.3: Clean `docs/openapi.yaml` duplicates and add examples. — owner:
    Backend, estimate: 3–5 days
- [ ] **Epic B — Core chat pipeline & short-term memory**
  - [ ] Story B.1: Implement POST /chat end-to-end with basic TTS/ASR mocked. — owner:
    Backend/FE, estimate: 5 days
  - [ ] Story B.2: Short-term memory API (add/list/delete) with canonical quotas. —
    owner: Backend, estimate: 4 days
  - [ ] Story B.3: E2E smoke tests and memory recall tests. — owner: QA, estimate: 3
    days
- [ ] **Epic C — Long-term memory, meditation, and pruning**
  - [ ] Story C.1: Memory ranking and nightly "meditation" rotation. — owner: Backend,
    estimate: 6 days
  - [ ] Story C.2: Long-term persistence and retention/migration tests. — owner:
    Backend, estimate: 4 days
- [ ] **Epic D — Agent skeleton & safety**
  - [ ] Story D.1: Agent runner prototype with quotas (Scheduler, Researcher). — owner:
    Backend, estimate: 5 days
  - [ ] Story D.2: Sandboxing + failure handling + quotas enforcement. — owner:
    SRE/Security, estimate: 4 days

## In Progress

- [ ] (Move items here when started)

## Done

- [ ] (Move items here when completed)

## Sprint Mapping

- **Sprint 1**: A.1, B.1, B.2
- **Sprint 2**: A.2, A.3, B.3, C.1
- **Sprint 3**: C.2, D.1, D.2

Update this file as work progresses. For automation, consider migrating to GitHub
Projects once issues are created.
