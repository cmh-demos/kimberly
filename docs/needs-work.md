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
