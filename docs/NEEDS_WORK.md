# Needs work — prioritized

This file lists the highest-priority documentation and project gaps I found, with short assessments and next actions. Updated after backend implementation (JWT auth, memory scoring/meditation, agent delegation, expanded testing, infra fleshing).

## Top priority (fix now)
- README placeholders: add dev quickstart + runnable example (why: onboarding friction). Next: add install, env, run steps and example `curl` and test data. (Consolidated: Also replace "Download app (TBD)" with platform decision, e.g., PWA for mobile.)
- `docs/openapi.yaml` dedupe & clean: remove duplicate schemas, complete error responses (why: client SDK generation breaks). Next: run OpenAPI linter and add examples. (Consolidated: Remove remaining duplicate requestBody entries; complete all paths/schemas; validate with openapi-generator.)
- Incomplete OpenAPI spec: schemas cut off mid-definition, duplicates present (why: API clients unreliable). Next: complete all endpoints/schemas and validate.
- CHANGELOG.md placeholder: Populate with recent changes (e.g., backend implementation). Why: Version tracking missing. Next: Add entries for new features (auth, memory, agents).
- FEATURES.md typo: Fix "-### Memory Management" header. Why: Formatting error. Next: Correct to "###".

## High priority (this sprint)
- Sprint-plan: attach owners + measurable acceptance criteria (why: QA/ownership). Next: turn into tickets with owners. (Consolidated: Assign real owners to RISK_ANALYSIS.md TBDs, e.g., @backend-dev.)
- Diagrams missing: add component and sequence Mermaid diagrams (why: clarify architecture & flows). Next: embed sample mermaid diagrams in ARCHITECTURE.md. (Consolidated: Create missing diagrams/wireframes; use Mermaid for more flows.)
- No CI/CD pipelines: no .github/workflows or automated builds/tests (why: no validation). Next: add GitHub Actions for linting, testing, OpenAPI validation. (Consolidated: Add CI doc checks with markdownlint; implement review cycle script for TBDs/placeholders.)
- Wireframes missing: referenced SVGs not present in workspace (why: UI design blocked). Next: create/add wireframes as described in wireframes/README.md. (Consolidated: Create text-based placeholders or ASCII art.)
- Testing expansion: current tests cover basics; need AI-specific tests, hallucination checks, bias detection (why: model QA incomplete). Next: add testing matrix in TESTING.md, implement AI validation tests.

## Medium priority
- Branding implementation: Develop and apply visual identity (why: consistent user experience). Next: Create logo variations, apply color palette to wireframes, and gather feedback on branding guidelines. (Consolidated: Finalize brand assets in BRANDING.md; integrate into UI mocks and marketing materials.)
- CI checks for docs & APIs (openapi lint, doc build, copilot_tracking validation). Next: add GitHub Actions or CI-agnostic pipeline. (Consolidated: Implement automated linting for docs; add CI for dependency scanning.)
- ML implementation completion: memory scoring/meditation implemented; need LLM integration and evaluation scripts (why: core ML untested). Next: integrate hybrid LLM approach (local Llama 3.1 8B primary, API fallback), add evaluation scripts.
- Infra deployment: Terraform fleshed for local; need Oracle Always Free configs and production manifests (why: can't deploy to free cloud). Next: add Oracle Always Free Terraform, Helm charts for production.
- Security hardening: JWT auth added; need encryption-at-rest, KMS design, detailed threat model (why: risks partially mitigated). Next: implement AES encryption, add KMS flows, update threat model.
- Metrics/telemetry setup: Prometheus/Grafana in infra; need integration and benchmarks (why: can't measure success yet). Next: integrate logging, establish latency/uptime benchmarks.
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

## Completed in recent backend work
- **Code implementation**: Basic runnable app with FastAPI, JWT auth, chat endpoint, memory management, agent delegation. (Previously: no code at all.)
- **Memory scoring & meditation**: Implemented scoring logic and nightly pruning engine. (Previously: no ML code.)
- **Agent orchestration**: Basic agent runner with quotas and safety controls. (Previously: no agent code.)
- **Testing expansion**: Test suite expanded from 2 to 11 tests covering auth, memory, agents. (Previously: minimal testing.)
- **Infra fleshing**: Terraform config for local k3s deployment with Postgres, Redis, MinIO, monitoring. (Previously: skeleton only.)
- **Security basics**: JWT authentication, password hashing, and rate limiting prep. (Previously: no auth.)

## Additional Outstanding Items (from rescan)
- **LLM Integration**: Hybrid approach decided (local Llama 3.1 8B primary, API fallback); app uses mock responses. Next: Implement local inference integration, add API wrapper fallback, create evaluation scripts.
- **Database Integration**: PostgreSQL + pgvector decided with migration path to dedicated vector DB if needed. Next: Implement schema design, connection logic, and vector search integration.
- **Encryption Implementation**: No encryption-at-rest; sensitive data not encrypted. Next: Implement AES encryption for memory content and KMS for keys.
- **Logging Integration**: No structured logging; no integration with Loki/Prometheus. Next: Add logging middleware and metrics emission.
- **CI/CD Completion**: .github/workflows exists but incomplete (only lint job). Next: Add test, build, deploy jobs for staging/production.
- **Diagrams in ARCHITECTURE.md**: Placeholder Mermaid diagrams present but not embedded. Next: Add actual component and sequence diagrams.
- **FEATURES.md Typo Fix**: "-### Memory Management" should be "###". Next: Correct header formatting.
- **OpenAPI Spec Validation**: Spec exists but may have duplicates/incompletes. Next: Run linter and complete all schemas.
- **README Quickstart Update**: Basic quickstart present but may need auth examples. Next: Add JWT token examples and real usage.
- **CHANGELOG Population**: Basic structure but missing recent backend features. Next: Add entries for auth, memory, agents, infra.
- **AI-Specific Tests**: No hallucination, bias, or accuracy tests. Next: Add AI validation tests and evaluation scripts.
- **Metrics Integration**: Prometheus/Grafana in infra but not integrated in code. Next: Add metrics endpoints and logging.
- **Environment Configuration**: No .env examples or production configs. Next: Add environment setup docs and variable management.
- **Production Deployment**: Only local Terraform; no Oracle Always Free or Fly.io configs. Next: Add cloud-specific Terraform modules.
- **Backup & Recovery**: No automated backups or restore procedures. Next: Implement DB backups and test restores.
- **Compliance Documentation**: No GDPR/CCPA docs or audit trails. Next: Create compliance checklists and audit logging.
- **Accessibility Features**: No WCAG compliance or screen reader support. Next: Add accessibility guidelines and tests.
- **Wireframes Validation**: SVG files exist but may not match requirements. Next: Review and update wireframes per ui-design.md.
- **Free-Mode Enforcement**: No checks to prevent paid API usage. Next: Add CI grep rules and runtime checks.

## Additional Quality-Related Work Proposals

- **Code Reviews & Standards Enforcement**: Implement mandatory code reviews with checklists for PEP 8 compliance, static analysis, and security scans to ensure code quality. (Consolidated: Create `docs/CODE_REVIEW.md` with approval rules.)
- **Risk Mitigation Tracking**: Regularly update RISK_ANALYSIS.md and create GitHub issues for high-priority risks with assigned owners and deadlines.
- **Bug Tracking & Monitoring System**: Set up a centralized bug tracking system (e.g., GitHub Issues with labels) and integrate real-time monitoring dashboards for errors, performance, and usage metrics.
- **Accessibility Audits**: Conduct WCAG 2.1 AA compliance audits for all UI components and add automated accessibility testing tools. (Consolidated: See UI/UX details.)
- **Performance Benchmarking**: Establish benchmarks for latency, uptime, and scalability against SUCCESS_CRITERIA.md KPIs, with regular load testing and profiling. (Consolidated: See metrics/telemetry.)
- **Markdown Linting**: Implement automated linting for docs. Why: Consistency and errors. Next: Add markdownlint-cli to CI.

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

- **Containerization Missing**: No Dockerfiles for services (app, memory, AI). Why: Can't containerize for K8s. Next: Add multi-stage Dockerfiles with Python base images.
- **Incomplete K8s Manifests**: Only meditation CronJob exists; no Deployments, Services, Ingress, ConfigMaps, Secrets. Why: Can't deploy full stack. Next: Add manifests for API, DB, Redis, workers.
- **No Helm Charts**: No Helm packaging for K8s deployments. Why: Manual deployments error-prone. Next: Create Helm chart with values for environments.
- **CI/CD Incomplete**: GitHub Actions has lint/test/OpenAPI; missing build (Docker), deploy to staging/prod. Why: No automated deployment. Next: Add build job, deploy to free cloud (Oracle/Fly.io).
- **Monitoring Not Configured**: Prometheus/Grafana mentioned but no configs/dashboards. Why: No visibility into performance. Next: Add Prometheus rules, Grafana dashboards for latency/uptime.
- **Logging/Traces Missing**: Loki/Tempo not set up. Why: Hard to debug issues. Next: Configure log aggregation and tracing.
- **Secrets Management**: No KMS/Vault integration. Why: Insecure key handling. Next: Use cloud KMS or SOPS for secrets.
- **Backups Absent**: No automated DB/object store backups or restore tests. Why: Data loss risk. Next: Add cron scripts for dumps, monthly restore drills.
- **Networking Incomplete**: No Ingress controller, load balancing. Why: No external access. Next: Add NGINX Ingress, service meshes.
- **Security Policies**: No network policies, RBAC, service mesh. Why: Vulnerable to attacks. Next: Implement Istio or Calico for security.
- **Auto-Scaling Missing**: No HPA for pods. Why: Can't handle load spikes. Next: Add HPA based on CPU/memory.
- **Environment Configs**: No dev/staging/prod configs. Why: Hard to manage environments. Next: Add .env files, ConfigMaps per env.
- **Cost Monitoring**: No tracking for free-tier usage. Why: Accidental overages. Next: Integrate cost tools (e.g., AWS Cost Explorer analogs).
- **Compliance Tools**: No audit logging, GDPR automation. Why: Non-compliant. Next: Add audit trails, data export tools.

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

## SRE-Specific Gaps

As a site reliability engineer, I've identified the following gaps in reliability, scalability, monitoring, incident response, and operational readiness. These address the project's goals for 99.9% availability, <150ms memory retrieval latency, and graceful failure handling.

- **App Startup Failure Debugging**: App exits with code 1 on run (python app.py); no logs or error output captured. Why: Unreliable deployment and testing. Next: Add try/except in app.py for startup errors, log to stderr/file; run with verbose flags to capture stack traces; fix root cause (e.g., Redis connection, missing env vars).
- **Metrics Integration in Code**: No Prometheus metrics emitted from app.py (e.g., request latency, error rates, memory ops). Why: No quantitative monitoring. Next: Add prometheus-client library; instrument endpoints with counters/histograms; expose /metrics endpoint.
- **Alerting Setup**: No alerts configured for failures (e.g., app crashes, queue depth > threshold). Why: Reactive incident response. Next: Configure Prometheus Alertmanager rules for SLO breaches; integrate with email/Slack for on-call notifications.
- **Incident Runbooks Development**: Outlines exist in ops-and-observability.md but no detailed playbooks for common issues (e.g., DB outage, agent failure). Why: Slow MTTR. Next: Expand runbooks with step-by-step actions, escalation paths, and post-mortems; test via tabletop exercises.
- **Backup & Recovery Implementation**: No automated backups for Postgres/Redis/object store; no restore tests. Why: Data loss risk. Next: Add cron jobs for DB dumps; implement point-in-time recovery; schedule monthly restore drills with verification.
- **Chaos Engineering & Load Testing**: No resilience testing (e.g., kill pods, simulate failures) or load benchmarks. Why: Unknown failure modes under stress. Next: Use Chaos Mesh for K8s; add k6/JMeter scripts for load testing against SLOs (e.g., 1000 req/s).
- **Security Hardening**: Encryption-at-rest not implemented; no KMS for keys; JWT auth present but no audit logging. Why: Data breaches possible. Next: Implement AES for memory data; integrate cloud KMS (e.g., AWS KMS); add audit trails for sensitive ops.
- **Scalability Testing & Auto-Scaling**: No HPA or load balancing; untested under concurrent users. Why: Can't handle growth to 10k interactions. Next: Add K8s HPA based on CPU; test with Locust for concurrency; optimize DB queries for vector searches.
- **Monitoring Dashboards**: Grafana mentioned but no actual dashboards for latency, errors, usage. Why: Hard to diagnose issues. Next: Create dashboards for API metrics, memory tiers, agent performance; integrate with Loki for logs.
- **On-Call Procedures**: No defined on-call rotation or escalation. Why: Unclear ownership for incidents. Next: Define on-call schedule (even if solo); add PagerDuty or email alerts; document handoff procedures.
- **Dependency Vulnerability Scanning**: No automated scans for Python packages (e.g., via Snyk, Safety). Why: Exposed to known CVEs. Next: Add CI job for vuln scans; pin dependencies in requirements.txt; update regularly.
- **Performance Benchmarking**: No baselines for latency/uptime against SUCCESS_CRITERIA.md. Why: Can't measure improvements. Next: Establish benchmarks (e.g., p95 <150ms); add profiling (e.g., py-spy) for bottlenecks; monitor regressions in CI.
- **Observability for AI/ML**: No metrics for model inference latency, hallucination rates, or agent safety. Why: Black-box AI risks. Next: Instrument Llama 3.1 calls; add custom metrics for bias/hallucination detection; log agent executions.
- **Free-Tier Cost Monitoring**: No tracking for cloud usage (e.g., Oracle Always Free limits). Why: Accidental overages. Next: Integrate cost monitoring tools; add alerts for usage thresholds; enforce free-mode in code.
- **Compliance Automation**: No GDPR export/purge APIs or audit logs. Why: Legal risks. Next: Implement data export/import endpoints; add retention policies; automate compliance checks.
