# 12-Week (4–12 week) Roadmap — Kimberly (MVP-first)

Goal: Deliver a safe, single-user MVP for conversational AI with robust short-term memory and initial agent orchestration. This 12-week plan breaks the work into three 4-week phases (12 weeks total) so you can choose 4, 8, or 12 week scope from the same structure.

## Phase A — Weeks 1–4: Foundations (MVP minimal)
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

## Phase B — Weeks 5–8: Stability & memory expansion
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

## Phase C — Weeks 9–12: Agent workstreams & beta preparation
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

## Cross-cutting priorities
- Security & privacy first (local-first by default, encryption options)
- Telemetry for KPIs (latency, memory relevance, agent task success)
- Tests & automation (95% coverage target for core services in phases B–C)

## How to use this plan
- 4-week delivery = Phase A + acceptance
- 8-week delivery = Phase A + B
- 12-week delivery = Full MVP + Beta

Owners, estimates, and ticketized backlog will be built next.
