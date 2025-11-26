# Architecture

This document describes system boundaries, major components, data flows, integrations,
and constraints.

## Goals

- Scalability, observability, security, and maintainability.

## Components

- API Gateway: ingress, routing, authentication, rate-limiting.
- AI Service: Handles conversational AI using hybrid LLM approach - primary local
  inference with Llama 3.1 8B quantized model, API wrapper fallback for high-demand
  scenarios.
- Services: auth, user, billing, jobs, reporting (each service is a small, well-scoped
  container).
- Data stores: PostgreSQL with pgvector (primary relational + vector), Redis
  (cache/session), object storage (S3-compatible) for blobs.
- Background processing: worker fleet consuming from a durable queue (e.g.,
  Kafka/RabbitMQ).
- Observability: Prometheus (metrics), Grafana (dashboards), ELK/Tempo for logs/traces.

## Data flow (high-level)

1. Client -> API Gateway (TLS, auth)
2. Gateway routes to service; services talk to databases or enqueue background jobs
3. Background workers process jobs and emit events/metrics

## Deployment

- Container images (Docker), Kubernetes for orchestration.
- Infrastructure as code: Terraform for cloud resources.
- CI/CD: build images, run tests, deploy to staging then production via automated
  pipelines.

## Diagrams

The following Mermaid diagrams illustrate the system architecture and key data flows.

### System Component Diagram

```mermaid
graph TB
  subgraph Clients
    Web[Web Browser]
    Mobile[Mobile PWA]
    Voice[Voice Assistant]
  end

  subgraph Gateway Layer
    API[API Gateway<br/>TLS, Auth, Rate-limit]
  end

  subgraph Core Services
    Auth[Auth Service]
    Users[User Service]
    Chat[AI/Chat Service<br/>Llama 3.1 8B]
    Billing[Billing Service]
    Memory[Memory Service]
    Agents[Agent Orchestrator]
  end

  subgraph Background Processing
    Queue[(Message Queue<br/>Kafka/RabbitMQ)]
    Worker[Worker Fleet]
  end

  subgraph Data Stores
    Postgres[(PostgreSQL<br/>+ pgvector)]
    Redis[(Redis<br/>Cache/Session)]
    S3[(Object Storage<br/>S3-compatible)]
  end

  subgraph Observability
    Prometheus[Prometheus]
    Grafana[Grafana]
    Logs[ELK/Tempo<br/>Logs & Traces]
  end

  Web -->|HTTPS| API
  Mobile -->|HTTPS| API
  Voice -->|HTTPS| API

  API --> Auth
  API --> Users
  API --> Chat
  API --> Billing
  API --> Memory
  API --> Agents

  Auth --> Redis
  Auth --> Postgres
  Users --> Postgres
  Chat --> Memory
  Chat --> Postgres
  Memory --> Postgres
  Memory --> Redis
  Billing --> Postgres
  Billing --> Queue
  Agents --> Queue
  Agents --> Chat

  Worker --> Queue
  Worker --> Postgres
  Worker --> S3

  Auth -.-> Prometheus
  Users -.-> Prometheus
  Chat -.-> Prometheus
  Memory -.-> Prometheus
  Worker -.-> Prometheus
  Prometheus --> Grafana
  Auth -.-> Logs
  Chat -.-> Logs
```

### Simplified Data Flow

```mermaid
graph LR
  Client -->|HTTPS| API[API Gateway]
  API --> Auth[Auth Service]
  API --> Users[User Service]
  API --> Chat[AI Service]
  API --> Memory[Memory Service]
  Users --> Postgres[(PostgreSQL)]
  Auth --> Redis[(Redis Cache)]
  Memory --> Postgres
  Chat --> Memory
  Worker[Worker] --> Queue[(Message Queue)]
  Worker --> S3[(Object Storage)]
```

## Sequence Diagrams

### Sign-up Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant Users as User Service
    participant DB as PostgreSQL

    Client->>API: POST /signup (email, password)
    API->>Auth: Validate input
    Auth->>Users: Create user
    Users->>DB: Insert user record
    DB-->>Users: Success
    Users-->>Auth: User created
    Auth-->>API: JWT token
    API-->>Client: 201 Created + token
```

### Login Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant DB as PostgreSQL

    Client->>API: POST /login (email, password)
    API->>Auth: Authenticate
    Auth->>DB: Query user
    DB-->>Auth: User data
    Auth->>Auth: Verify password
    Auth-->>API: JWT token
    API-->>Client: 200 OK + token
```

### Chat Conversation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant Chat as AI/Chat Service
    participant Memory as Memory Service
    participant DB as PostgreSQL
    participant LLM as Llama 3.1 8B

    Client->>API: POST /chat (message)
    API->>Auth: Validate JWT
    Auth-->>API: Valid
    API->>Chat: Process message
    Chat->>Memory: Retrieve relevant context
    Memory->>DB: Query memories (hybrid search)
    DB-->>Memory: Memory items
    Memory-->>Chat: Context data
    Chat->>LLM: Generate response (message + context)
    LLM-->>Chat: AI response
    Chat->>Memory: Store conversation
    Memory->>DB: Insert short-term memory
    Chat-->>API: Response + usage
    API-->>Client: 200 OK + response
```

### Memory Retrieval Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Memory as Memory Service
    participant DB as PostgreSQL
    participant Cache as Redis

    Client->>API: POST /memory/query (query, filters)
    API->>Memory: Query request
    Memory->>Cache: Check cache
    alt Cache hit
        Cache-->>Memory: Cached results
    else Cache miss
        Memory->>DB: Metadata filter + FTS
        DB-->>Memory: Candidate items
        Memory->>Memory: Hybrid re-rank (score + recency)
        Memory->>Cache: Store results
    end
    Memory-->>API: Top-K results
    API-->>Client: 200 OK + results
```

### Agent Delegation Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Chat as AI/Chat Service
    participant Agents as Agent Orchestrator
    participant Queue as Message Queue
    participant Worker as Background Worker
    participant DB as PostgreSQL

    Client->>API: POST /chat (task request)
    API->>Chat: Process request
    Chat->>Chat: Detect agent-suitable task
    Chat->>Agents: Delegate to agent
    Agents->>Agents: Check concurrent limit (max 3)
    Agents->>Queue: Enqueue agent task
    Agents-->>Chat: Task ID
    Chat-->>API: Acknowledge + task ID
    API-->>Client: 202 Accepted + task ID

    Queue->>Worker: Process task
    Worker->>Worker: Execute agent logic
    Worker->>DB: Store results
    Worker-->>Queue: Task complete

    Client->>API: GET /agents/tasks/{task_id}
    API->>DB: Query task status
    DB-->>API: Task result
    API-->>Client: 200 OK + result
```

### Billing Flow

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Billing as Billing Service
    participant DB as PostgreSQL
    participant Queue as Message Queue
    participant Worker as Background Worker

    Client->>API: POST /billing/subscribe (plan)
    API->>Billing: Process subscription
    Billing->>DB: Update user billing
    DB-->>Billing: Success
    Billing->>Queue: Enqueue payment job
    Queue-->>Worker: Process payment
    Worker->>Worker: Charge payment gateway
    Worker-->>DB: Record transaction
    Worker-->>API: Notify success (via webhook or poll)
    API-->>Client: 200 OK + confirmation
```

### Memory Meditation (Nightly Scoring) Flow

```mermaid
sequenceDiagram
    participant Scheduler as Cron/Scheduler
    participant Worker as Meditation Worker
    participant DB as PostgreSQL
    participant Metrics as Prometheus

    Scheduler->>Worker: Trigger nightly meditation
    Worker->>DB: Fetch user memory items
    DB-->>Worker: Memory items batch

    loop For each memory item
        Worker->>Worker: Compute relevance_to_goals
        Worker->>Worker: Compute emotional_weight
        Worker->>Worker: Compute predictive_value
        Worker->>Worker: Compute recency_freq
        Worker->>Worker: Calculate weighted score
        Worker->>DB: Update item score
    end

    Worker->>DB: Get tier quotas
    DB-->>Worker: Quota limits

    loop For each tier over quota
        Worker->>Worker: Sort by ascending score
        Worker->>DB: Archive lowest-scoring items
        Worker->>DB: Mark for deletion (grace period)
    end

    Worker->>Metrics: Report meditation.processed
    Worker->>Metrics: Report meditation.pruned
    Worker-->>Scheduler: Meditation complete
```

## Constraints and trade-offs

- Prefers managed cloud services for operational simplicity.
- K8s adds operational overhead but gives scaling and isolation.
- Performance targets: Chat response <1s (warm model), initial model load <30s, memory
  retrieval <500ms, agent delegation <5s, meditation <10min.

## API Overview

This document provides a concise overview of the Kimberly REST API and links to the
OpenAPI definition in `docs/openapi.yaml`.

### Authentication

- JWT Bearer tokens (issued on login/signup).
- All protected endpoints require `Authorization: Bearer <token>`.

### Core endpoints (summary)

- POST /signup — create an account and receive JWT
- POST /login — authenticate and receive JWT
- POST /chat — send a message to the conversational AI
- GET /memory — list memory items
- POST /memory — add memory
- DELETE /memory/{id} — remove memory
- GET /agents — list available agents
- POST /agents/{id}/run — invoke an agent
- GET /health — service health

For full request/response details and schemas see `docs/openapi.yaml`.

### Publishing container images (CI-agnostic)

- Recommended registry: GitHub Container Registry (`ghcr.io`) — provider-agnostic and
  well-supported for private and public images.
- Use explicit, immutable tags (eg. `ghcr.io/<org>/kimberly:<semver>-<sha>`) and a
  stable `latest` branch tag for development flows.
- Keep CI pipelines vendor-agnostic; any CI system that can build, test, sign
  (optional), and push to `ghcr.io` will work. Avoid bake-in to a single provider at
  this stage.
