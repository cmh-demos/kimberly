---
title: "Infrastructure design — Kimberly & Memory Manager (free-first)"
---

# Kimberly infra — Memory Manager focused design (free-first)

Status: Draft

Summary
-------
This document lays out an infrastructure design for Kimberly and the Memory Manager with a strong preference for free / free‑tier hosting. The design supports local development, low‑cost MVP hosting and a path to production-ready managed services when budgets or scale demand it.

Goals
-----
- Start small: free resources for dev and early users, easy local dev story.
- Portability: portable Terraform + K8s manifests so providers can be swapped.
- Safety & privacy: encryption, audit trails, and user controls built-in.
- Scalability path: clear migrations from self-hosted free VMs to managed cloud services.

High-level architecture
-----------------------
Core components:
- API gateway (ingress + TLS + auth)
- Application services (auth, users, billing, jobs, memory, agents) deployed as containers on Kubernetes
- Memory subsystem (three-tier design):
  - Short-term: Redis (in-memory cache), extremely low latency, ephemeral
  - Long-term / Permanent: PostgreSQL (metadata + pgvector for small‑scale vectors) or optional standalone vector store
  - Object store (S3-compatible, e.g., MinIO for self-hosted or provider-managed S3 for cloud)
- Worker fleet: background processing for jobs and nightly meditation (scoring) — horizontally scalable workers
- Observability: Prometheus + Grafana for metrics; Loki/ELK+Tempo for logs & traces (OSS stack)
- CI/CD: GitHub Actions (pipeline: build → tests → publish GHCR images → deploy to staging → promote to prod)

Network & security
------------------
- Deploy in a VPC/subnet with private services (DBs, Redis) not exposed publicly.
- Use TLS for all ingress and mTLS or service account tokens for in-cluster service-to-service communication.
- Secrets: use cloud provider KMS or a secrets manager (SOPS/Vault) for dev and Vault/SSM/KMS in prod.
- RBAC for admin interfaces (agents, memory manager) and explicit consent & audit logging for all memory writes/deletes.

Storage, retrieval & vector search
---------------------------------
Start (free / simple):
- Postgres with pgvector extension (single instance or managed free-tier Postgres if available) — keeps storage and vector search in one place, easiest to manage and migrate.
- Redis for short-term caching and fast session context.
- MinIO as an S3-compatible object store for attachments and transcripts (runs well on small VMs).

Scale / optional upgrades:
- Swap pgvector to a managed vector DB (Pinecone, Weaviate, Milvus) when vector size or query throughput outgrows Postgres.
- Introduce replication and read-replicas for Postgres; move large blob storage to provider-managed object storage (S3) for scale & durability.

Free-first deployment options (recommended order)
------------------------------------------------
1) Local dev — zero cost (recommended to iterate quickly)
   - kind or k3d for Kubernetes local cluster
   - Postgres (pgvector) via Helm chart
   - MinIO Helm chart for S3-like storage
   - Redis via Helm chart
   - Run nightly meditation as a K8s CronJob

2) Free-cloud bootstrap (low ops, low cost):
   - Oracle Cloud Always Free: small VMs + block storage (run k3s or k0s) — low ops and truly free for early proof-of-concept
   - Fly.io: if you prefer a simpler managed app platform (uses per-app VMs, easy deploy, quick setup). ADR already suggests Fly.io.

3) Small managed services (free-tier friendly) for staging:
   - GitHub Actions for CI + GHCR for container registry (already recommended)
   - Managed Postgres free-tier (if available) or small instance on provider's free tier
   - Use MinIO or provider's free object storage tier

Production guidance (when budgets allow)
-------------------------------------
- Use managed K8s (EKS/GKE/AKS) for large fleets to reduce ops burden, or a managed platform (Fly, Render, Railway) with HA if you prefer PaaS.
- Managed Postgres with pgvector or a managed vector DB (Pinecone/Weaviate) when scale/throughput requires it.
- Backups: regular DB and object store snapshots with cross-region retention and tested restores.

Operational patterns
--------------------
- Nightly meditation pipeline (K8s CronJob or scheduled worker): compute scores for memory items and run retention policies
- Backup schedule and verification job; keep 30‑90 day backups depending on compliance
- Alerts & SLOs: memory-tier usage, meditation success/failure, vector store latency, queue backlog, and worker failures
- Cost controls: per-user quotas, throttles, rate-limiting at gateway, and alerts when approaching quota thresholds

Implementation notes (dev -> staging -> prod)
--------------------------------------------
Dev: run everything in kind/k3d with local ports and a developer secrets file (and optionally a local Vault)
Staging: run on small provider VMs or Fly.io with managed DB and GHCR
Prod: deploy against managed cloud (EKS/GKE/AKS or managed K8s service) with multi-AZ replicas and a managed vector DB if necessary

Open choices & tradeoffs
------------------------
- pgvector vs dedicated vector DB: pgvector is free/small-scale friendly but less performant at very large vector sizes. Vector DBs give better performance and features at cost.
- Self-hosted K8s on free VMs (Oracle Always Free) offers near-zero cost but higher ops burden vs Fly.io or managed K8s which cost money but lower ops.
- Logging and tracing: ELK/Loki/Tempo are free to run but may be heavy; for small deployments, use lightweight aggregators and host logs for limited retention.

Next steps
----------
1. Pick target bootstrap environment (local dev + Oracle Always Free or Fly.io).  
2. Create a minimal IaC skeleton (Terraform modules + k8s manifests + Helm releases) that targets the free-first bootstrap.  
3. Add CI (GitHub Actions) to build images and deploy to a staging environment.  

Reference files in this repo
---------------------------
- `docs/deployment-appendix.md` — existing notes recommending Oracle Always Free and Fly.io
- `docs/decisions/ADR-0004.md` — deployment model decision in this repo
- `docs/memory-model.md` — canonical memory model we must implement and support

Design owner
------------
Infra / SRE — infra@kimberly.local (placeholder)
