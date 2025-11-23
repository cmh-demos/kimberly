# Kimberly — Risk Analysis & Unknowns Tracker

This document captures known risks for the Kimberly project and tracks the important unknowns that need investigation. It is intended to be a living artifact linked from the `README.md` and used as an operational checklist for product, security, and engineering owners.

Last updated: 2025-11-22

## Purpose

- Surface the top technical, operational, security, and product risks that will cause delivery, user harm, or financial impact.
- Prioritize mitigations and short-term actions (quick wins) so the team can reduce risk rapidly.
- Track unknowns (open questions) with owners and next actions so the team knows what to investigate and why it matters.

## Scope

This analysis covers the codebase and design artifacts in this repository, the chosen architecture (Kubernetes + microservices + Llama 3.x), and non-functional goals (latency, uptime, privacy, compliance). It is NOT a substitute for a formal security audit or legal compliance review — those should be scheduled separately.

---

## How to use this file

- Update the `Status` column in the risk register regularly (weekly at a minimum) and add new risks as they appear.
- Add owners (GitHub handles or names) and target mitigation dates to make progress measurable.
- When a risk is discovered in the wild (incident or test failure), append a short post-mortem note (date + description) below the risk entry.

---

## Severity & Likelihood definitions

- Impact (Severity): Critical / High / Medium / Low — describes business or user harm if the risk occurs.
- Likelihood: Likely / Possible / Unlikely — how probable the risk is given current state.
- Priority: Calculated from Impact x Likelihood; this document highlights Critical/High risks first.

## Risk Register (prioritized)

| ID | Risk | Category | Impact | Likelihood | Priority | Mitigation(s) | Detection | Owner | Status |
|----|------|----------|--------|------------|----------|---------------|-----------|-------|--------|
| R-001 | No runnable implementation / primarily docs | Product / Delivery | Critical | Likely | Critical | Build a minimal end-to-end PoC using a hosted LLM to validate flows and developer on-ramps. Create quickstart in README. | PR/CI checks, demo readiness | @owner TBD | Active — high | 
| R-002 | Unrealistic non-functional goals (latency <1s, 99.9% uptime at early-stage) | Product / Architecture | High | Likely | High | Re-scope SLOs; run latency benchmarks on a PoC; consider hosted models for low-latency MVP. | Performance tests; benchmark reports | @owner TBD | Active — validation needed |
| R-003 | LLM deployment cost & infra mismatch (Llama 3.1 inference hardware & licensing) | Cost / Infrastructure | High | Likely | High | Produce cost estimate for self-hosting vs hosted provider; plan GPU sizing; track licensing/redistribution constraints. | Cost run rates, infra invoices | @ops TBD | Active — investigate |
| R-004 | Security: E2E encryption claims without KMS/key management design | Security / Privacy | Critical | Possible | Critical | Draft KMS design, add key rotation, encryption-at-rest + in-transit diagrams, threat model. Limit telemetry to redacted PII. | Security reviews, pen-test | @sec TBD | Active — fix design |
| R-005 | GDPR & data deletion gaps — no verified deletion/export flow | Legal / Compliance | Critical | Possible | Critical | Implement a data export & deletion endpoint; add audit logging and automated tests to prove deletion. | Manual/automated deletion checks, compliance review | @data_privacy TBD | Active — needs implementation |
| R-006 | OpenAPI duplication & schema issues breaking SDK/clients | Developer Experience | High | Likely | High | Lint & fix openapi.yaml; add CI lint step, add a sample client generation check in CI. | CI validation failure | @api TBD | Active — fix in progress |
| R-007 | No CI pipelines for tests/quality/validation | Developer Experience / Risk | High | Likely | High | Add GitHub Actions for linting, unit tests, openapi validation, copilot_tracking schema checks. | PR checks status | @dev TBD | Active — onboarding CI |
| R-008 | No AI-quality tests (hallucinations, bias, memory accuracy) | Quality | High | Likely | High | Create an AI test harness and regression suite (acceptance tests for memory correctness, hallucination detection, fairness checks). | Test failures & regression alerts | @ml TBD | Planned |
| R-009 | Agent sandboxing insufficient — agents may leak secrets or take destructive actions | Security / Safety | Critical | Possible | Critical | Define agent capability model, deny list for I/O, require policy enforcement and per-agent resource limits (CPU, memory, network). | Unit tests, agent traces, policy violation alerts | @engineering TBD | Active — design required |
| R-010 | Backup & Disaster Recovery untested (RPO/RTO unknown) | Operations | High | Possible | High | Document RPO/RTO, implement daily backups, periodic restore drills, store backups encrypted and off-site. | Restore drills, backup health metrics | @ops TBD | Planned |

---

## Unknowns (what we don't know yet) — prioritized checklist

These unknowns are important to resolve because they materially change mitigation and architecture decisions.

1. Hardware & hosting assumptions for Llama 3.1
   - Why it matters: Determines cost, latency, and feasibility of on-prem model inference.
   - Info needed: Model size to be used, expected concurrency for target SLOs, GPU types and counts, memory/IO profiles, whether quantized model is acceptable.
   - Next action: Run a PoC benchmark with a small quantized model or measure hosted provider latency/cost; owner: @ml; target: 2 weeks.

2. Licensing and legal constraints for chosen LLM (weights, redistribution, commercial use)
   - Why: Could prevent shipping a self-hosted model or require vendor licensing costs.
   - Info needed: Llama 3.1 license and any third-party dependencies; vendor approval for commercial hosting if applicable.
   - Next action: Legal review and model license audit; owner: @legal; target: 1 week.

3. Concrete SLOs & realistic performance targets for MVP
   - Why: Determines architecture choices and cost tradeoffs.
   - Info needed: Real user patterns (expected daily/peak interactions), acceptable voice latency, acceptable percentiles (P50/P95), and acceptable cost per active user/day.
   - Next action: Product & engineering to agree on pragmatic SLOs; owner: @product; target: 1 week.

4. Data retention & deletion mechanics for GDPR/compliance
   - Why: Must be demonstrable (logs/tests) before any public-facing release.
   - Info needed: retention policies, audit trail locations, export format, deletion confirmation tests (end-to-end). 
   - Next action: Implement and test data deletion endpoint for demo data; owner: @data_privacy; target: 2 weeks.

5. Threat model for voice inputs and third-party integrations (calendars, email, GitHub)
   - Why: Agents and external services expand attack surface and need explicit constraints.
   - Info needed: OAuth flows, scoping decisions, token storage strategy, least-privilege plan.
   - Next action: Produce a one-page threat model; owner: @sec; target: 2 weeks.

6. Telemetry and logging privacy — exact fields collected in `misc/copilot_tracking.json` and data minimization policy
   - Why: Avoid PII leaks in telemetry and audits.
   - Info needed: Which fields contain PII? Can telemetry be sampled, redacted, or hashed? Retention policy for logs (required for incident research vs privacy law). 
   - Next action: Review telemetry schema & propose redaction rules; owner: @sec or @dev; target: 1 week.

7. CI/CD hosting & runners — which environment will run inference tests or integration tests that require GPUs
   - Why: CI that needs GPUs has different cost/ops implications (self-hosted runners vs cloud). 
   - Next action: Decide CI strategy for ML workloads; owner: @devops; target: 2 weeks.

8. Detailed agent orchestration model (capabilities, concurrency, isolation semantics)
   - Why: Agent behaviors are a safety and reliability risk; we need an explicit orchestration design.
   - Next action: Create an agent orchestration ADR and propose a minimal sandbox for the MVP; owner: @engineering; target: 3 weeks.

---

## Immediate short-term actions (quick wins to reduce highest risk)

- PoC runnable demo (hosted LLM) to verify latency & flow — target: 3 days. Owner: @ml / @dev.
- Add small GitHub Actions workflow to validate `docs/openapi.yaml` and `misc/copilot_tracking.json` against the schemas — target: 1–2 days. Owner: @dev.
- Add an explicit data deletion endpoint for demo data and automated test case proving deletion — target: 1 week. Owner: @data_privacy.
- Draft the one-page threat model and KMS design — target: 1 week. Owner: @sec.

## How we will track progress

- Add GitHub issues for the top unknowns and high-priority risks (R-001, R-004, R-005, R-006, R-007). Link those issues back in the `Owner` cell.
- During each sprint planning meeting, the owner will update the `Status` and estimate mitigation dates.

---

## Template: add/update a risk

When adding or updating a risk, include:
- short description + id
- category
- owner (GitHub handle) and target date
- current status and evidence (e.g., failing test, open incident)
- mitigations for short/medium/long term

---

If you'd like, I can also:
- create the GitHub issues for the top unknowns and high-priority risks, or
- add a CI workflow to validate the OpenAPI file and copilot schema immediately.

---

Document created by: repo:kimberly — automated snapshot analysis
