# Risk actions / investigation checklist

This checklist contains high-priority unknowns and suggested GitHub issue titles and descriptions to help the team assign and track the investigations required to reduce risk.

Owner guidance: create one GitHub Issue per checklist item and paste the issue URL below the item once open. Assign the issue to the suggested owner or a named person.

## Top unknowns to raise as issues

- [ ] Investigate Llama 3.1 hosting/benchmark (issue: `investigate/llama-hosting-benchmarks`) — produce latency & cost numbers for possible model sizes (quantized, non-quantized), expected concurrency, and recommended GPU types (cost estimate + runbook). Suggested owner: @ml or @devops.

- [ ] LLM licensing audit (issue: `audit/llm-licensing-and-legal`) — confirm license terms, redistribution and commercial use constraints for Llama 3.x and any dependencies. Suggested owner: @legal.

- [ ] Decide SLOs & profiling targets (issue: `tune/slo-definition-and-benchmarks`) — agree realistic P50/P95 latency targets and traffic patterns for MVP. Suggested owner: @product + @engineering.

- [ ] Data deletion & GDPR workflow (issue: `feature/data-deletion-and-export`) — design and implement an audited deletion/export API for user data and test harness. Suggested owner: @data_privacy.

- [ ] OpenAPI validation + CI enforcement (issue: `ci/openapi-lint-and-validation`) — fix schema dupes and add CI step to validate generated SDK. Suggested owner: @api.

- [ ] Telemetry redaction rules (issue: `security/telemetry-redaction-and-retention`) — propose privacy-preserving telemetry schema and retention settings. Suggested owner: @sec.

- [ ] Agent orchestration ADR + sandbox (issue: `arch/agent-orchestration-and-sandbox`) — write ADR, propose minimal sandbox for MVP, define deny-list and capability model. Suggested owner: @engineering.

- [ ] CI runners / hardware for ML tests (issue: `devops/ci-ml-runners`) — decide whether to use hosted runners or self-hosted GPU runners for model workloads in CI. Suggested owner: @devops.

## Next steps

1. Create the issues above in GitHub and link them back to this checklist file.
2. Add the issue links into `docs/RISK_ANALYSIS.md` Owner field where appropriate.

If you want, I can open the issues and add the first round of owners and acceptance criteria — tell me which items you'd like me to open as issues and I'll create the PRs.
