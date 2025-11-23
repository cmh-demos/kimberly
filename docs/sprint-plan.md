# 3‑Month Sprint Plan — Kimberly (MVP)

Goal: Deliver an MVP that supports voice + web conversations, robust short/long memory, and a safe agent orchestration layer — instrumented and ready for early users.

Timeline: 3 months (6 x 2-week sprints)

Sprint 0 (Prep — 1 week)
- Objectives: define acceptance criteria, finalize MVP scope, set up instrumentation, CI for logs/schema.
- Deliverables: PRD signoff, telemetry plan, test harness, append helper script for copilot logs.

Sprint 1 (Weeks 1–2)
- Objectives: Voice + Web basic chat pipeline, short-term memory implemented (see `docs/memory-model.md` for canonical quotas), local-first option.
- Deliverables: chat endpoint, voice TTS/ASR integration (basic), memory API, end‑to‑end tests.
- Acceptance: 1:1 chat with memory persists and recalled in same session. 95% test coverage for chat and memory modules.
- Owners: Backend (Alice), Frontend (Bob), QA (Charlie)

Sprint 2 (Weeks 3–4)
- Objectives: Long-term memory with prioritization and nightly "meditation" process; memory pruning (see `docs/memory-model.md` for canonical quotas).
- Deliverables: memory ranking system, persistence, migration scripts, privacy opt-outs.
- Acceptance: memory rotation tests + manual QA pass.

Sprint 3 (Weeks 5–6)
- Objectives: Agent orchestration core (Scheduler, Researcher, Coder), sandboxing and quotas.
- Deliverables: agent API, agent runner with quotas, failure-handling paths.
- Acceptance: agents perform tasks on synthetic workload without escapes or excessive resource use.

Sprint 4 (Weeks 7–8)
- Objectives: Instrumentation & monitoring for KPIs, error reporting, usage dashboards.
- Deliverables: telemetry pipeline, dashboard, alert thresholds, cost monitoring.
- Acceptance: dashboards show baseline metrics and alerts trigger on simulated anomalies.

Sprint 5 (Weeks 9–10)
- Objectives: Developer experience + privacy hardening, docs, tests, and a small closed beta.
- Deliverables: onboarding docs, SDK examples, consent flows, beta release process.
- Acceptance: closed beta with 10 users, feedback loop, iterate critical bug fixes.

Deliverables at end of 3 months
- Voice + web MVP, memory + agent basics, telemetry, docs, closed beta telemetry-based iteration.

Owners & roles (suggested)
- PM: roadmap & prioritization
- Eng lead: architecture and infra
- Backend: memory & agent services
- Frontend: web/voice UI
- SRE: telemetry/cost/observability
- Security/Privacy: consent & audits

Risks & Mitigations
- Over-scoped agents → limit to 2 core agents for MVP; design clear failure modes.
- Privacy concerns → default local-first memory; opt-in telemetry.
- Cost overruns → quota agents + sandbox + early cost monitoring.

Next steps (this sprint)
- Finalize owners & acceptance criteria
- Instrument baseline telemetry
- Kickoff Sprint 1 implementation

---

## Key KPIs (to track during these 3 months)

- MAU / DAU (activation & retention): track weekly active users and 7/30-day retention
- Task Success Rate (agents): percent of agent tasks that finish successfully without escalation
- Memory Relevance Score: user-verified accuracy of memory recall (via spot checks)
- Mean Response Latency: target < 500ms for local ops / < 2s for remote ops
- Error Rate & SLOs: API error rate < 1% and SLOs agreed with infra
- Privacy opt-in rate: percent of users choosing local-first storage vs cloud
- Telemetry coverage: % of flows instrumented (95% goal)
- CI/Test coverage: maintain > 80% unit test coverage for core services
- Cost per active user: track infra spend per DAU and set budget cap

Mapping KPIs to Sprints
- Sprint 1: Latency, basic response success, telemetry coverage begin
- Sprint 2: Memory relevance & recall benchmarks
- Sprint 3: Agent task success & quotas
- Sprint 4: Dashboards & error monitoring
- Sprint 5: Retention & closed beta metrics

Acceptance criteria and a measurable target should be attached to each KPI before beta.

---

If you want, I’ll convert this into a short Jira-like backlog with prioritized tickets and owners next.  
