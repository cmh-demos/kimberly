# Needs work — prioritized

This file lists the highest-priority documentation and project gaps I found, with short assessments and next actions.

## Top priority (fix now)
- README placeholders: add dev quickstart + runnable example (why: onboarding friction).  Next: add install, env, run steps and example `curl` and test data.
- `docs/openapi.yaml` dedupe & clean: remove duplicate schemas, complete error responses (why: client SDK generation breaks).  Next: run OpenAPI linter and add examples.
- No code implementation: entire codebase missing; only docs and scripts exist (why: can't run/test anything). Next: implement minimal runnable app (e.g., Python API with Llama 3.1 integration).
- Incomplete OpenAPI spec: schemas cut off mid-definition, duplicates present (why: API clients unreliable). Next: complete all endpoints/schemas and validate.

## High priority (this sprint)
- Sprint-plan: attach owners + measurable acceptance criteria (why: QA/ownership).  Next: turn into tickets with owners.
- Diagrams missing: add component and sequence Mermaid diagrams (why: clarify architecture & flows).  Next: embed sample mermaid diagrams in ARCHITECTURE.md.
- No CI/CD pipelines: no .github/workflows or automated builds/tests (why: no validation). Next: add GitHub Actions for linting, testing, OpenAPI validation.
- Minimal testing: only one test file; no unit/integration/E2E for core features (why: no functionality validation). Next: add test suites (e.g., pytest) for 95% coverage, including AI tests.
- Wireframes missing: referenced SVGs not present in workspace (why: UI design blocked). Next: create/add wireframes as described in wireframes/README.md.

## Medium priority
- CI checks for docs & APIs (openapi lint, doc build, copilot_tracking validation).  Next: add GitHub Actions or CI-agnostic pipeline.
- AI tests: memory accuracy, hallucination checks, bias detection (why: model QA).  Next: add testing matrix in TESTING.md.
- ML implementation details: no code for memory scoring, meditation, LLM integration (why: core ML untested). Next: implement scoring logic, local Llama inference, evaluation scripts.
- Infra artifacts incomplete: Terraform/Helm/K8s skeletons but no executable configs (why: can't deploy). Next: flesh out for free providers, add manifests.
- Security & threat model: basic SECURITY.md, no detailed model or KMS (why: risks unmitigated). Next: add threat model, encryption flows.
- Metrics/telemetry implementation: KPIs defined but no tracking code (why: can't measure success). Next: add Prometheus/Grafana, integrate logging.
- Agent orchestration: no code or sandbox for delegation (why: agents unsafe). Next: implement runner with quotas/isolation.

## Lower priority / Nice to have
- Mobile plan: fill TBD in README with platform choices and distribution path.
- Add more examples & SDK snippets in `docs/API.md`.
- Documentation completeness: some files placeholders (e.g., CHANGELOG.md); ADRs brief (why: maintenance harder). Next: expand with examples, add ADRs.
- UI/UX details: no prototypes or accessibility tests (why: UI dev stalled). Next: build HTML/CSS mocks, add WCAG checklist.
- Data pipelines & ops: no ETL, backups, restore tests (why: data fragile). Next: add export/import scripts, automated backups.
- Free-mode enforcement: no CI blocks for paid APIs (why: accidental costs). Next: add grep-based rules.
- Project management: plans exist but no tickets/owners (why: execution unclear). Next: convert to GitHub issues.

## Notes and assessment
- Most gaps are documentation and validation gaps (fixes are straightforward). The openapi dedup + tests are most important to enable SDK and CI.
- New gaps identified include major implementation holes (code, ML, infra) that shift priority toward building a prototype.

If you want, I can convert each top-priority item into tickets/PRs and start with README + OpenAPI cleanup.

## Finance / Budget clarifying questions (add to backlog)
These are the questions the finance manager needs to build a budget — add as follow-up items or checklist before budgeting work begins:

- Timeframe: monthly, quarterly, or annual? Preferred horizon (3 / 12 / 36 months)?
- Level of detail: high-level P&L vs line-item budget (staffing, infra, marketing, contractors)?
- Currency & target accuracy: which currency, and accuracy target (ballpark, draft, audited)?
- Existing data: is there an existing finance file (CSV/Excel) or accounting export to import? If so, where?

## UX / UI — Outstanding questions (add to backlog)

These questions inform the UI design and are necessary to finalize wireframes, flows and acceptance criteria.

- Target platforms and priority: do we want web-only for MVP or simultaneous web+mobile (native or PWA) and voice? (Why: layout decisions and interaction patterns)
- Default memory UX: should chat messages be saved automatically, or should we require an explicit "Save to memory" action? If automatic, what UX should indicate saved state and consent?
- Memory quotas & visual presentation: what are the default per-user quotas (confirmed values vs. the ones listed in memory-model)? How should we visualize quotas and thresholds in the UI?
- Archival/restore policy UX: how should the archive / restoration flow work for normal users vs power users (one-click restore, multi-item bulk operations, auto-expiry notifications)?
- Agent safety model: what agent privilege levels and sandbox policies must the UI enforce or expose? Do we need role-based UI changes for admin vs end user?
- Embeddings and self-hosted mode: when embeddings are enabled (self-hosted only), should the UI show an explicit hosting indicator and an audit trail for vector ingestion? How should the opt-in flow work?
- Privacy & consent microcopy: do we have legal-approved language for consent toggles and export/purge confirmations (GDPR / privacy)?
- Onboarding & education: how much onboarding is required to explain memory tiers, meditation, and scoring (short text tips vs a multi-step guided flow)?
- Accessibility target level: confirm WCAG level (minimum WCAG 2.1 AA recommended) and whether voice-first flows are required for the MVP.
- Branding / visual system: do we have brand colors, typography, iconography to include in mocks (or should we create a neutral placeholder system)?

Next work items (UX deliverables):
- Create low-fidelity wireframes for Chat, Memory Manager, and Agents (desktop + mobile) — acceptance: annotated wireframes added to `docs/` and a simple PNG export.
- Create high-fidelity mockups (Figma file or HTML/CSS) for final screens and accessible styles — acceptance: link or static prototype published.
- Accessibility checklist & tests — acceptance: WCAG checklist in `docs/` and a short list of automated/manual tests.

## Infra / Ops — Outstanding questions (add to backlog)

These questions guide infrastructure decisions, bootstrapping, and production readiness for Kimberly and the Memory Manager.

- Target hosting: preferred bootstrap target (Oracle Always Free, Fly.io, local-only, or a cloud provider like AWS/GCP/Azure)?
- Workloads and partitioning: confirm services to host in cluster vs managed services (memory service, AI model service, web API, workers, agent runtime).
- Scale and performance targets: expected requests/sec, typical concurrency, expected average memory size per user, and projected data growth over 3/12/36 months?
- Availability/SLA: single-region vs multi-AZ vs multi-region, and RTO/RPO targets for stateful services?
- Security/compliance: any mandatory requirements (PII/GDPR, HIPAA, PCI, SOC2) that impose retention, encryption, or auditing constraints?
- Cost and budget: clarifying budget for infra (strictly free, free+low cost, or enterprise budget) and preferred free-tier choices.
- Storage choices: pgvector in Postgres vs dedicated vector DB (Pinecone/Weaviate/Milvus) — preference and thresholds for moving off pgvector.
- Backups and restore policy: frequency, retention, and whether automated restore verification is required (eg. monthly test restores).
- Nightly meditation & daily processing: how long can the meditation job run (time windows), and what grace/soft-delete period is required for pruned items?
- Secrets and key management: prefer cloud KMS, HashiCorp Vault, or SOPS/local secrets for dev?
- CI/CD & provisioning: confirm GitHub Actions with GHCR for images, or alternate CI provider? Should Terraform provisioning be automated via CI?
- Observability targets: target SLOs (availability, memory retrieval latency), metrics retention, and alerts thresholds/granularity.
- Data sovereignty & multi-region constraints: are there geographic restrictions on where user memory data can be stored?
- Operator model: who will run and operate infra (team size, on-call, runbook ownership)?
- Integration & migration constraints: are there existing production databases or services that must be integrated or migrated?
- Quotas and abuse controls: expected or required default per-user quotas and escalation process when quotas are exceeded.

Next: convert these questions into tracked tickets and assign owners before implementing changes.

## Implementation Questions (add to backlog)

These questions clarify technical details needed for coding the core features, ML components, and integrations.

- Core tech stack: What programming language and framework for the API (e.g., Python FastAPI, Node.js Express) and ML components (e.g., PyTorch, Hugging Face)?
- LLM specifics: Which Llama 3.1 variant (e.g., 8B, 70B, quantized) and integration method (local inference, API wrapper)? Licensing and redistribution details?
- Memory scoring implementation: How to compute the weighted scoring formula (libraries like scikit-learn, custom logic)? Data sources for components (relevance, emotion, recency)?
- Meditation process: How to run nightly scoring/pruning (cron job, background worker)? Handling of archived items and quota enforcement?
- Agent delegation: How are agents implemented (subprocesses, APIs, containers)? Isolation/sandboxing mechanisms (e.g., Docker, resource limits)? Communication protocols?
- Database schema: Detailed schema for MemoryItem, users, conversations? Migrations and versioning?
- Embeddings: How to implement optional self-hosted embeddings (e.g., sentence-transformers, FAISS)? Default disabled, but opt-in flow?
- Security encryption: Methods for encrypting sensitive memory data (e.g., AES, KMS integration)? Key management for local vs cloud?
- Voice integration: Libraries for TTS/ASR (e.g., ElevenLabs, open-source like Coqui TTS)? Latency targets and fallback handling?
- UI tech stack: Frameworks for web (e.g., React, Vue), mobile (native, PWA), and voice interfaces?
- Data pipelines: ETL for memory ingestion, export/import formats (e.g., JSON, CSV)? Handling large transcripts or attachments?
- Testing tools: Specific tools for AI validation (e.g., bias detection with AIF360, hallucination checks with custom scripts)?
- Observability integration: How to instrument code for Prometheus metrics, logging, and tracing?
- Free-mode constraints: Exact rules for blocking paid APIs in code (e.g., environment flags, runtime checks)?
- Backup/restore: Automated scripts for DB dumps, object store snapshots, and restore verification?
- CI/CD specifics: Beyond GitHub Actions, any custom scripts or tools for ML model testing/deployment?

Next: prioritize and assign owners to these questions for implementation planning.
