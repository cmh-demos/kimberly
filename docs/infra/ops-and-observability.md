# Observability, backups, alerts & runbook guidance — Kimberly

This document describes pragmatic observability, backup, SLOs, and on-call/runbook guidance suitable for free-first and small-scale deployments.

Monitoring & metrics
--------------------
- Metrics stack (free / OSS friendly): Prometheus + Grafana.
- Metrics to collect:
  - Memory Manager: per-user storage usage per tier, number of memory items, meditation run durations, items pruned per run
  - Vector store: query latency, QPS, top-K values, cache hit rate (if used)
  - DB: connections, replication lag, long queries
  - Worker queues: queue depth, rate of processing, error rates
  - API gateway: request latencies, 5xx/4xx rates, rate-limiting events

Logging & tracing
-----------------
- Stack options (OSS-friendly): Grafana Loki (logs) + Tempo (traces) or an ELK stack.
- Log retention: short defaults for free tier (7–30 days), configurable depending on requirements and cost.

Alerting
--------
- Examples (alert if any triggers):
  - Meditation job failure or high latency (> 1 min)
  - Postgres storage > 80% and > 90% (warning + critical)
  - Queue length > N (depends on worker scale) for > 10 minutes
  - Vector search p50/p99 latency > acceptable thresholds
  - Backup job failures

SLOs & Service targets
----------------------
- Availability (for the API): 99.9% for paid / production; 99% for small free-tier deployments
- Memory retrieval latency: p95 < 150ms (pgvector small-scale), tightens if using managed vector DB
- Meditation success rate: daily runs should complete within a configured window (e.g., <= 10 minutes)

Backups & disaster recovery
---------------------------
- Postgres: daily dumps and point-in-time recovery when supported.
- Object store: versioned buckets or snapshot replication to secondary storage.
- Test restores at least monthly; automate restore verifications when possible.

Runbooks & incident playbooks
----------------------------
- Runbook: Memory tier burst overflow
  - Symptoms: memory-tier quota alarms, failed POST /memory requests with quota errors
  - Immediate actions: identify offending user(s), throttle or increase quota temporarily, kick off a manual meditation prune for that user
  - Recovery: run a backfill meditation if needed; notify customer if data purged

- Runbook: Meditation job failed
  - Symptoms: CronJob reports failed runs, metrics show unprocessed queued items
  - Immediate actions: check job logs, restart job, scale policymakers (workers), verify DB connectivity
  - Recovery: re-run meditation job manually, check sample outputs for correctness

CI/CD & deployment tips
-----------------------
- Use GitHub Actions as CI (repo prefers it) and GHCR for container registry.
- Pipeline stages:
  - unit tests + lint
  - integration tests (in ephemeral kind cluster) — optional
  - build, tag, push image to GHCR
  - deploy to staging and run smoke tests
  - promote to production with an approval step

Cost controls & lowering ops
---------------------------
- Enforce per-user quotas early to prevent abuse.
- Use pgvector for early workloads to avoid extra managed services cost.
- Keep logs/metrics retention short for free-tier deployments but schedule exports if required for compliance.

Next steps & checklist
----------------------
1. Add Prometheus + Grafana helm charts to the `local` dev stack.
2. Add monitoring exporters (Postgres, Redis, Kubernetes metrics-server) in manifests.
3. Add a GitHub Actions pipeline skeleton for building images and deploying to dev/staging clusters.
