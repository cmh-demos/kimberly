# Roadmap

## High-Level Milestones and Releases

- MVP: Basic conversational chat, memory management, and simple coding problem solving.
- v1: Long-term memory, basic agent delegation, and expanded coding capabilities.

Timeline: Q1 2026 for MVP release.

## Detailed Roadmap

- Q4 2025: Prototype core chat and memory.
- Q1 2026: MVP release with basic agents.
- Q2 2026: v1 with advanced features.
- Q3 2026: Beta testing and refinements.
- Q4 2026: Full launch.

## 12-Week (4–12 week) Roadmap — Kimberly (MVP-first)

Goal: Deliver a safe, single-user MVP for conversational AI with robust short-term memory and initial agent orchestration. This 12-week plan breaks the work into three 4-week phases (12 weeks total) so you can choose 4, 8, or 12 week scope from the same structure.

### Phase A — Weeks 1–4: Foundations (MVP minimal)

- Objectives:
  - Implement conversational chat API (web + basic voice pipeline)
  - Implement short-term memory (session-priority, see `docs/memory-model.md` for canonical quotas and behaviors) and local-first option
  - Basic developer UX: quickstart README, runnable example, and tests
- Deliverables:
  - POST /chat API working end-to-end, basic TTS/ASR integration (mocked acceptable)
  - Memory API (add/list/delete), short-term persistence, memory recall tests
  - Readme Quickstart + e2e smoke test and docs
- Acceptance:
  - 1:1 chat with memory accessible within a session; integration test passes

### Phase B — Weeks 5–8: Stability & memory expansion

- Objectives:
  - Add long-term memory ranking & nightly "meditation" rotations
  - Add basic monitoring, CI checks (openapi lint, schema validation, copilot log validation)
  - Implement simple agent runner skeleton (Scheduler, Researcher)
- Deliverables:
  - Memory ranking system + persistence and migration scripts
  - CI checks for docs/openapi and core tests; baseline dashboards
  - Agent runner prototype with quotas and sandboxing
- Acceptance:
  - Automated nightly rotation tests and CI passes in main flows

### Phase C — Weeks 9–12: Agent workstreams & beta preparation

- Objectives:
  - Extend agent ecosystem (add Coder agent), agent error handling and isolation
  - Hardening: privacy flows, security audit checklist, test coverage targets
  - Developer beta & onboarding materials (closed beta run)
- Deliverables:
  - Stable agent APIs and operator controls for quotas/retries
  - Privacy & consent flows; QA checklist and security notes
  - Beta onboarding docs and SDK snippets
- Acceptance:
  - Closed beta with instrumentation: KPIs tracked, onboarding docs validated by 5 users

### Cross-cutting priorities

- Security & privacy first (local-first by default, encryption options)
- Telemetry for KPIs (latency, memory relevance, agent task success)
- Tests & automation (95% coverage target for core services in phases B–C)

### How to use this plan

- 4-week delivery = Phase A + acceptance
- 8-week delivery = Phase A + B
- 12-week delivery = Full MVP + Beta

Owners, estimates, and ticketized backlog will be built next.

## Prioritized Backlog — next 3 sprints (6 weeks)

This backlog converts audit findings into epics and prioritized user stories for the next three sprints (Sprint 1–3 in the 3-month plan). Owners and rough estimates are suggested; we can convert these into GitHub issues next.

### Epic A — Developer onboarding & CI (High priority)

- Story A.1: Create a runnable Quickstart + example (README + test harness). — owner: Docs/FE, estimate: 2 days
- Story A.2: Add CI checks: openapi linter, docs build, copilot_tracking schema validation. — owner: SRE, estimate: 3 days
- Story A.3: Clean `docs/openapi.yaml` duplicates and add examples. — owner: Backend, estimate: 3–5 days

### Epic B — Core chat pipeline & short-term memory (Highest priority)

- Story B.1: Implement POST /chat end-to-end with basic TTS/ASR mocked. — owner: Backend/FE, estimate: 5 days
- Story B.2: Short-term memory API (add/list/delete) with canonical quotas (see `docs/memory-model.md`) — owner: Backend, estimate: 4 days
- Story B.3: E2E smoke tests and memory recall tests. — owner: QA, estimate: 3 days

### Epic C — Long-term memory, meditation, and pruning (High)

- Story C.1: Memory ranking and nightly "meditation" rotation. — owner: Backend, estimate: 6 days
- Story C.2: Long-term persistence (canonical quotas — see `docs/memory-model.md`) and retention/migration tests. — owner: Backend, estimate: 4 days

### Epic D — Agent skeleton & safety (Medium)

- Story D.1: Agent runner prototype with quotas (Scheduler, Researcher) — owner: Backend, estimate: 5 days
- Story D.2: Sandboxing + failure handling + quotas enforcement — owner: SRE/Security, estimate: 4 days

### Sprint plan mapping (6-week view)

- Sprint 1: A.1, B.1, B.2 (quickstart, chat API, short-term memory)
- Sprint 2: A.2, A.3, B.3, C.1 (CI checks, openapi, tests, meditation prototype)
- Sprint 3: C.2, D.1, D.2 (long-term memory hardening, agents skeleton, sandboxing)

### Next steps I can take (select 1)

- Create GitHub issues for each story with labels and owners.
- Open PRs for Quickstart README + CI changes.
- Break down stories into sub-tasks and acceptance criteria.

## Risks

- AI model availability: Mitigate by selecting stable open-source models (e.g., Llama) with fallbacks; monitor community updates and plan for model upgrades.
- Scalability challenges: Mitigate with Kubernetes auto-scaling, load testing, and performance profiling; cap initial user load.
- User adoption: Mitigate through beta testing feedback, iterative improvements, and clear documentation; focus on single-user personalization.

## Success Criteria

KPIs and acceptance tests for the MVP and v1 releases.

### MVP Success Criteria

- Conversational accuracy: 90% correct responses in test scenarios.
- Memory retention: 95% recall of short-term memories after 24 hours.
- Response latency: <1 second average.
- Uptime: 99.9% availability.
- User satisfaction: 4.5/5 rating in beta tests.

### V1 Success Criteria

- Agent delegation success: 85% tasks completed autonomously.
- Long-term memory accuracy: 90% relevant recall.
- Scalability: Handle 10,000 daily interactions without degradation.
- Security: Zero data breaches in testing.
- Compliance: Pass all GDPR and accessibility audits.
