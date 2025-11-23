# Needs work — prioritized

This file lists the highest-priority documentation and project gaps I found, with short assessments and next actions.

## Top priority (fix now)
- README placeholders: add dev quickstart + runnable example (why: onboarding friction). Next: add install, env, run steps and example `curl` and test data. (Consolidated: Also replace "Download app (TBD)" with platform decision, e.g., PWA for mobile.)
- `docs/openapi.yaml` dedupe & clean: remove duplicate schemas, complete error responses (why: client SDK generation breaks). Next: run OpenAPI linter and add examples. (Consolidated: Remove remaining duplicate requestBody entries; complete all paths/schemas; validate with openapi-generator.)
- No code implementation: entire codebase missing; only docs and scripts exist (why: can't run/test anything). Next: implement minimal runnable app (e.g., Python API with Llama 3.1 integration).
- Incomplete OpenAPI spec: schemas cut off mid-definition, duplicates present (why: API clients unreliable). Next: complete all endpoints/schemas and validate.
- CHANGELOG.md placeholder: Populate with recent changes (e.g., app.py addition). Why: Version tracking missing. Next: Add entries for unreleased features.
- FEATURES.md typo: Fix "-### Memory Management" header. Why: Formatting error. Next: Correct to "###".

## High priority (this sprint)
- Sprint-plan: attach owners + measurable acceptance criteria (why: QA/ownership). Next: turn into tickets with owners. (Consolidated: Assign real owners to RISK_ANALYSIS.md TBDs, e.g., @backend-dev.)
- Diagrams missing: add component and sequence Mermaid diagrams (why: clarify architecture & flows). Next: embed sample mermaid diagrams in ARCHITECTURE.md. (Consolidated: Create missing diagrams/wireframes; use Mermaid for more flows.)
- No CI/CD pipelines: no .github/workflows or automated builds/tests (why: no validation). Next: add GitHub Actions for linting, testing, OpenAPI validation. (Consolidated: Add CI doc checks with markdownlint; implement review cycle script for TBDs/placeholders.)
- Minimal testing: only one test file; no unit/integration/E2E for core features (why: no functionality validation). Next: add test suites (e.g., pytest) for 95% coverage, including AI tests. (Consolidated: Create `docs/TESTING_PROCESS.md` for workflows; add pytest suite for API endpoints.)
- Wireframes missing: referenced SVGs not present in workspace (why: UI design blocked). Next: create/add wireframes as described in wireframes/README.md. (Consolidated: Create text-based placeholders or ASCII art.)

## Medium priority
- CI checks for docs & APIs (openapi lint, doc build, copilot_tracking validation). Next: add GitHub Actions or CI-agnostic pipeline. (Consolidated: Implement automated linting for docs; add CI for dependency scanning.)
- AI tests: memory accuracy, hallucination checks, bias detection (why: model QA). Next: add testing matrix in TESTING.md.
- ML implementation details: no code for memory scoring, meditation, LLM integration (why: core ML untested). Next: implement scoring logic, local Llama inference, evaluation scripts.
- Infra artifacts incomplete: Terraform/Helm/K8s skeletons but no executable configs (why: can't deploy). Next: flesh out for free providers, add manifests. (Consolidated: Flesh out Terraform for Oracle Always Free; add Helm charts for services; create `docs/ENVIRONMENT_SETUP.md` for per-env guides, including credential setup.)
- Security & threat model: basic SECURITY.md, no detailed model or KMS (why: risks unmitigated). Next: add threat model, encryption flows. (Consolidated: Implement threat model and KMS design; add encryption-at-rest/in-transit; create `docs/COMPLIANCE.md` for checklists.)
- Metrics/telemetry implementation: KPIs defined but no tracking code (why: can't measure success). Next: add Prometheus/Grafana, integrate logging. (Consolidated: Establish benchmarks for latency/uptime; create `docs/PERFORMANCE_MONITORING.md` for setup guides.)
- Agent orchestration: no code or sandbox for delegation (why: agents unsafe). Next: implement runner with quotas/isolation.
- Docs consistency: Standardize formatting and add "Last Updated" dates. Why: Inconsistent style. Next: Audit and fix headers/links.
- Cross-references: Add internal links (e.g., FEATURES.md to memory-model.md). Why: Navigation poor. Next: Update with relative links.
- Examples/snippets: Add code examples to API.md and TESTING.md. Why: Friction for devs. Next: Include curl/pytest samples.
- ADR expansion: Flesh out ADRs with pros/cons. Why: Decision rationale weak. Next: Add alternatives and outcomes.

## Lower priority / Nice to have
- Mobile plan: fill TBD in README with platform choices and distribution path.
- Add more examples & SDK snippets in `docs/API.md`. (Consolidated: Add inline examples like curl snippets.)
- Documentation completeness: some files placeholders (e.g., CHANGELOG.md); ADRs brief (why: maintenance harder). Next: expand with examples, add ADRs. (Consolidated: Fill TBDs in docs; create process docs like `docs/ONBOARDING.md`, `docs/CODE_REVIEW.md` (with security checklists), `docs/RELEASE_PROCESS.md`, `docs/INCIDENT_RESPONSE.md`, `docs/COMMUNICATION.md`, `docs/BACKUP_RECOVERY.md`, `docs/ACCESSIBILITY.md`, `docs/DEPENDENCY_MANAGEMENT.md`, `docs/CHANGE_MANAGEMENT.md`, `docs/USER_FEEDBACK.md`.)
- UI/UX details: no prototypes or accessibility tests (why: UI dev stalled). Next: build HTML/CSS mocks, add WCAG checklist. (Consolidated: Conduct WCAG 2.1 AA audits; create accessibility guidelines.)
- Data pipelines & ops: no ETL, backups, restore tests (why: data fragile). Next: add export/import scripts, automated backups. (Consolidated: Implement daily DB backups with restore tests; add data export/import procedures.)
- Free-mode enforcement: no CI blocks for paid APIs (why: accidental costs). Next: add grep-based rules.
- Project management: plans exist but no tickets/owners (why: execution unclear). Next: convert to GitHub issues.

## Additional Quality-Related Work Proposals

- **Code Reviews & Standards Enforcement**: Implement mandatory code reviews with checklists for PEP 8 compliance, static analysis, and security scans to ensure code quality. (Consolidated: Create `docs/CODE_REVIEW.md` with approval rules.)
- **Risk Mitigation Tracking**: Regularly update RISK_ANALYSIS.md and create GitHub issues for high-priority risks with assigned owners and deadlines.
- **Bug Tracking & Monitoring System**: Set up a centralized bug tracking system (e.g., GitHub Issues with labels) and integrate real-time monitoring dashboards for errors, performance, and usage metrics.
- **Accessibility Audits**: Conduct WCAG 2.1 AA compliance audits for all UI components and add automated accessibility testing tools. (Consolidated: See UI/UX details.)
- **Performance Benchmarking**: Establish benchmarks for latency, uptime, and scalability against SUCCESS_CRITERIA.md KPIs, with regular load testing and profiling. (Consolidated: See metrics/telemetry.)
- **Markdown Linting**: Implement automated linting for docs. Why: Consistency and errors. Next: Add markdownlint-cli to CI.
- **Review Cycle Implementation**: Create a script to scan for gaps (TBDs, placeholders). Why: Proactive maintenance. Next: Add Python script in scripts/ for doc health checks.

## Notes and assessment
- Most gaps are documentation and validation gaps (fixes are straightforward). The openapi dedup + tests are most important to enable SDK and CI.
- New gaps identified include major implementation holes (code, ML, infra) that shift priority toward building a prototype.

If you want, I can convert each top-priority item into tickets/PRs and start with README + OpenAPI cleanup.

## Finance / Budget clarifying questions (add to backlog)
These are the questions the finance manager needs to build a budget — add as follow-up items or checklist before budgeting work begins:

- Timeframe: monthly, quarterly, or annual? Preferred horizon (3 / 12 / 36 months)?
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

## Security Recommendations from Review

Based on a security engineering review of project progress, the following recommendations are prioritized for implementation to address critical risks and ensure secure development.

### Immediate (Sprint 1)
- Implement threat model and KMS design (addresses R-004 in RISK_ANALYSIS.md). Add encryption-at-rest/in-transit to architecture. Draft data deletion/export API with audit logging. Next: Create docs/threat-model.md and update ARCHITECTURE.md with encryption details.

### Short-Term (Sprints 2-3)
- Build minimal runnable PoC with security-first (e.g., JWT auth, input sanitization). Add CI for dependency scanning (Snyk) and OpenAPI linting. Enforce free-mode (no paid APIs) with grep checks. Next: Implement auth in API code, add GitHub Actions workflows, and CI rules to block paid providers.
- Set up GitHub Secrets for CI pipelines (e.g., HUGGINGFACE_TOKEN). Why: Secure credential access in automated builds. Next: Add secrets in repo settings and reference in .github/workflows/ci.yml.
- Add pre-commit hooks for secret detection (e.g., detect-secrets). Why: Prevent accidental commits of credentials. Next: Install pre-commit, configure hooks in .pre-commit-config.yaml.

### Medium-Term
- Develop agent sandbox (resource limits, deny lists) and test harness for hallucinations/bias. Conduct security audit (pen-test) before MVP. Add observability for anomalies (e.g., failed meditations). Next: Design sandbox in agent runner, add AI validation tests, schedule audit.
- Integrate production secrets management (e.g., AWS Secrets Manager or Oracle Vault). Why: Secure key storage in production. Next: Choose provider, update code to retrieve secrets at runtime.

### Ongoing
- Embed security reviews in PRs. Monitor for new risks (e.g., LLM licensing constraints). Ensure telemetry redaction and retention policies. Next: Add security checklist to CONTRIBUTING.md, review telemetry schema for PII.
- Conduct regular security reviews and audits. Why: Ongoing risk mitigation. Next: Schedule quarterly reviews, update RISK_ANALYSIS.md.

### Tools/Actions
- Use tools like `mcp_pylance_mcp_s_pylanceSyntaxErrors` for code validation; add security extensions (e.g., install_extension for Snyk). Create GitHub issues for top unknowns in RISK_ANALYSIS.md. Next: Install Snyk extension, run syntax checks on scripts, and open issues for unknowns.

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

## Additional Gaps from Rescan

Based on a deeper scan of the codebase, documentation, and infrastructure, the following gaps were identified that are not yet recorded in the needs-work file.

### Dependency and Environment Management
- No `requirements.txt` or `pyproject.toml` in root (README references `requirements.txt` but it doesn't exist). Why: Dependencies not declared, hard to install/reproduce. Next: Create `requirements.txt` with core deps (e.g., fastapi, sqlalchemy, sentence-transformers for optional embeddings).
- No `.gitignore` file. Why: Sensitive files (secrets, logs) may be committed accidentally. Next: Add standard Python .gitignore excluding .venv, __pycache__, secrets, and misc/copilot_tracking.json if sensitive.
- No `LICENSE` file (README claims MIT). Why: Legal clarity missing. Next: Add MIT LICENSE file.

### Containerization and Deployment
- No `Dockerfile` or `docker-compose.yml`. Why: No containerized builds/deployments. Next: Add Dockerfile for API service and docker-compose for local dev stack.
- IaC skeletons incomplete: Terraform `main.tf` is placeholder; no executable Helm charts. Why: Can't deploy to K8s. Next: Flesh out Terraform for Oracle Always Free, add Helm charts for services.

### Code Security and Quality
- Scripts lack input validation (e.g., `append_log.py` --note arg not sanitized). Why: Potential command injection or malformed JSON. Next: Add argparse validation and sanitization.
- No main application code (only scripts/docs). Why: No runnable product. Next: Implement minimal FastAPI app with chat/memory endpoints.
- Telemetry privacy risk: `misc/copilot_tracking.json` notes may contain PII. Why: GDPR violation. Next: Redact or encrypt notes; add retention policy.

### API and Testing
- OpenAPI spec incomplete (cuts off at line 600, missing some endpoints). Why: Incomplete API docs. Next: Complete all paths/schemas, validate with openapi-generator.
- No CI/CD workflows (no `.github/workflows`). Why: No automated tests/builds. Next: Add GitHub Actions for pytest, linting, OpenAPI validation.
- Minimal testing: Only one test file; no integration/E2E. Why: No validation of features. Next: Add pytest suite for API endpoints, memory logic.

### Documentation and Compliance
- Many placeholders/TBD in docs (e.g., mobile plan, branding). Why: Incomplete guidance. Next: Fill TBDs with decisions (e.g., PWA for mobile).
- No `CODE_OF_CONDUCT.md` or issue/PR templates. Why: Community standards missing. Next: Add standard templates for contributions.
- No backup/restore scripts or data export/import. Why: Data fragility. Next: Add scripts for DB dumps, JSON export/import.

## Infrastructure and Ops
- No monitoring/alerting setup (Prometheus/Grafana mentioned but not configured). Why: No observability. Next: Add Helm charts for monitoring stack.
- No disaster recovery plan (backups untested). Why: Data loss risk. Next: Implement daily DB backups with restore tests.

### Recommendations
- Add glossary.md for terms like "lexical," "normalization."
- Replace placeholders with real values.
- Provide examples/diagrams for clarity.
- Cross-link ambiguous sections (e.g., memory-model to API.md).

## Additional Ambiguities Identified

The following ambiguities were found during a comprehensive scan of all docs. They include undefined terms, placeholders, vague specs, and inconsistencies that could hinder implementation or understanding.

### Undefined Terms and Concepts
- **Normalization in Scoring (docs/memory-model.md)**: Scoring formula uses "normalize(...)" but doesn't specify method (e.g., min-max, z-score). Why: Inconsistent implementations. Next: Define normalization (e.g., min-max to 0-1).
- **Lexical Retrieval (docs/memory-model.md)**: "Lexical-first retrieval" unclear (full-text search, keywords?). Why: Retrieval logic ambiguous. Next: Specify as SQLite FTS with examples.
- **Lambda in Re-Ranking (docs/memory-model.md)**: Hybrid formula has "lambda" but no default value. Why: Re-ranking weights undefined. Next: Set default lambda=0.5 with config guidance.
- **Freshness Boost (docs/memory-model.md)**: Mentioned but not defined (recency factor?). Why: Scoring incomplete. Next: Define as exponential decay on last_seen_at.
- **Goal Models (docs/memory-model.md)**: "Match against active goal models" vague. Why: Relevance unclear. Next: Clarify as user-defined goals or inferred intents.
- **Predictive Value (docs/memory-model.md)**: "Past-match usability" lacks measurement. Why: Scoring subjective. Next: Define as historical match rates from user feedback.
- **Seamless Task Handling (README.md)**: "Seamless" subjective. Why: Expectations unclear. Next: Specify as <500ms latency, no user intervention.
- **Privacy-Forward (docs/ui-design.md)**: Vague term. Why: UI principles ambiguous. Next: Define as user-controlled sharing, opt-in telemetry.
- **Provider-Agnostic (docs/deployment-appendix.md)**: Claims portability but gives specifics. Why: Migration unclear. Next: List supported providers and migration steps.

### Placeholders and Incomplete References
- **TBD Owners (Multiple Files)**: @backend-dev, @ml TBD in docs/RISK_ANALYSIS.md, docs/RISK_ACTIONS.md, docs/sprint-plan.md. Why: Accountability missing. Next: Assign from roles.md.
- **Fictional Emails/Contacts**: docs-team@kimberly.local in docs/memory-model.md; product-design@kimberly.local in docs/ui-design.md. Why: Unrealistic. Next: Replace with real contacts or remove.
- **Target User "Me" (PROJECT.md)**: "Target user: ... (me)" first-person. Why: Confusing for readers. Next: Rephrase to "project owner/developer".
- **FE Abbreviation (docs/backlog-next-3-sprints.md)**: "Docs/FE" likely Frontend. Why: Unclear. Next: Spell out "Documentation/Frontend".
- **TBD in README.md**: "Mobile: Download app (TBD)". Why: Incomplete. Next: Specify if planned or remove.
- **Missing Diagrams/Wireframes**: Referenced SVGs not present. Why: Design blocked. Next: Create/add as per wireframes/README.md.

### Vague Specifications and Defaults
- **Size Calculation (docs/memory-model.md)**: size_bytes undefined (content only?). Why: Quota enforcement unclear. Next: Define as len(content) + metadata overhead.
- **OSS Models for Embeddings (docs/memory-model.md)**: "Self-hosted OSS models" unspecified. Why: Implementation blocked. Next: Recommend SentenceTransformers MiniLM.
- **Weights in Scoring (docs/memory-model.md)**: Configurable but no adjustment guidance. Why: Tuning hard. Next: Add UI/config for user adjustments.
- **Grace Window (docs/memory-model.md)**: "Configurable (e.g., 30d)" no default. Why: Retention unpredictable. Next: Set default 30 days.
- **Free-Mode Enforcement (docs/needs-work.md)**: "No CI blocks for paid APIs". Why: Cost risks. Next: Add CI grep for paid API calls.
- **Prep Week Details (docs/sprint-plan.md)**: Sprint 0 vague. Why: Planning unclear. Next: Detail objectives (e.g., finalize PRDs).
- **SLO Re-Scoring (docs/infra/ops-and-observability.md)**: "Tightens" ambiguous. Why: Performance unclear. Next: Clarify as "improves" for managed DBs.

### Inconsistent or Overlapping Definitions
- **Quotas (docs/memory-model.md)**: Interactions unclear (short-term vs total). Why: Over-quota handling ambiguous. Next: Specify hierarchy (total > tier sums).
- **Agent Limits (PROJECT.md)**: "Isolation protocols" vague. Why: Safety unclear. Next: Define as sandboxing + resource caps.
- **Bias Mitigation (docs/threat-model.md, PROJECT.md)**: Techniques unspecified. Why: Ethics vague. Next: List checks (e.g., fairness audits).
- **Ethical AI (PROJECT.md)**: Broad. Why: Scope unclear. Next: Define as consent, no harm.
- **Roles Overlap (roles.md)**: Notes overlap but no specifics. Why: Assignment hard. Next: Specify overlaps (e.g., SRE/DevOps).

### Missing Context or Examples
- **Hybrid Retrieval Flow (docs/memory-model.md)**: Steps listed, no example. Why: Hard to implement. Next: Add sample query/output.
- **Meditation Frequency (docs/memory-model.md)**: "On-demand" triggers undefined. Why: Scheduling unclear. Next: Define as user-initiated or quota breach.
- **Threat Mitigations (docs/threat-model.md)**: High-level (e.g., "encryption"). Why: Incomplete. Next: Specify tools (AES-256, TLS 1.3).
- **API Examples (docs/API.md)**: Lacks inline examples. Why: Usage unclear. Next: Add curl snippets.
- **Success Criteria (docs/pm-cadence-and-metrics.md)**: KPIs defined, no baselines. Why: Measurement hard. Next: Add initial baselines.

### Recommendations
- Add glossary.md for terms like "lexical," "normalization."
- Replace placeholders with real values.
- Provide examples/diagrams for clarity.
- Cross-link ambiguous sections (e.g., memory-model to API.md).
