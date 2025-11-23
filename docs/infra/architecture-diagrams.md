# Architecture diagrams — Kimberly (Memory Manager focused)

This file contains two primary diagrams (component and sequence) describing the proposed infrastructure for Kimberly and the Memory Manager. Use these as a reference for design discussions and to generate more detailed deployment diagrams.

## Component diagram (high level)

```mermaid
graph LR
  subgraph Internet
    Client["Client (web, mobile, voice)"]
  end

  subgraph Edge
    Gateway["API Gateway / Ingress (TLS, auth, rate-limit)"]
  end

  subgraph Kubernetes Cluster
    APISvc["API Services (auth, user, billing, api)"]
    AIService["AI Service / Model Runner"]
    MemorySvc["Memory Service (tiered memory API)"]
    Workers["Workers (background jobs & meditation)"]
    Queue["Message Queue"]
  end

  subgraph Data Layer
    Postgres["Postgres + pgvector"]
    Redis["Redis - short-term cache"]
    ObjectStore["S3 / MinIO"]
    VectorStore["Optional: Vector DB - Pinecone / Milvus / Weaviate"]
  end

  subgraph Observability
    Prometheus["Prometheus"]
    Grafana["Grafana"]
    Loki["Loki / Logs"]
    Tempo["Tempo / Tracing"]
  end

  subgraph CI/CD
    GHCR["GHCR (image registry)"]
    CI["GitHub Actions (CI/CD pipelines)"]
  end

  Client -->|HTTPS| Gateway
  Gateway --> APISvc
  APISvc --> MemorySvc
  APISvc --> Postgres
  APISvc --> Redis
  APISvc --> ObjectStore
  MemorySvc --> Postgres
  MemorySvc -->|fast reads/writes| Redis
  MemorySvc -->|embeddings / search| VectorStore
  AIService --> VectorStore
  AIService --> Postgres
  Workers --> Queue
  Workers --> MemorySvc
  Workers --> Postgres

  APISvc -->|metrics| Prometheus
  MemorySvc -->|metrics| Prometheus
  Workers -->|metrics| Prometheus
  Prometheus --> Grafana
  APISvc --> Loki
  Workers --> Loki
  APISvc --> Tempo

  CI --> GHCR
  CI -->|deploy| APISvc

  click VectorStore "https://example.com/docs/vector-store-considerations" "Vector store notes"
```

Notes:
- Start with Postgres + pgvector to keep the initial stack free-friendly and simple.
- Redis is used for short-term memory and ultrafast context access.
- Vector store is optional early — add when embedding volume or throughput justifies it.
- Nightly meditation is run by `Workers` (CronJob or scheduled workers) to re-score items and prune/rotate per quota rules.

## Memory flow — sequence diagram

This sequence shows a common path: store a new memory from chat, how it is indexed/embedded, and the nightly meditation pruning.

```mermaid
sequenceDiagram
  participant U as User (Client)
  participant API as API Gateway
  participant M as Memory Service
  participant DB as Postgres (metadata)
  participant Emb as Embedding Service
  participant Vec as Vector Store / pgvector
  participant Q as Queue
  participant W as Worker (meditation)

  U->>API: POST /memory (content + metadata)
  API->>M: validate + persist metadata
  M->>DB: INSERT MemoryItem
  M->>Emb: request embedding (async/fast)
  Emb-->>M: embedding vector
  M->>Vec: upsert vector reference
  M-->>API: 201 Created + {id, score}

  Note over W,DB: Nightly meditation job runs (CronJob or scheduled worker)
  W->>DB: query candidate memory items
  W->>Emb: (re-)compute embeddings and signals
  W->>Vec: re-rank via similarity
  W->>DB: update scores + prune lowest-scoring per quota
  W->>Q: enqueue further pruning, snapshot, & audit actions
  Q->>Workers: perform deletes/archives and create audit records
```

Next steps / additional views
----------------------------
- Add provider-specific topology (Oracle Always Free k3s, Fly.io, AWS/GCP) if you want physical network, subnets, and managed service diagrams.  
- Add deployment views (CI/CD flow, GitHub Actions details) and scaling diagrams (autoscaler groups, read replicas for Postgres, vector DB cluster topology) on request.

Reference: canonical memory model is `docs/memory-model.md` — use that file as the single source for memory quotas, lifecycle, and pruning behaviour.
