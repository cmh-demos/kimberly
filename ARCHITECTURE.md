# Architecture

This document describes system boundaries, major components, data flows, integrations, and constraints.

## Goals
- Scalability, observability, security, and maintainability.

## Components
- API Gateway: ingress, routing, authentication, rate-limiting.
- AI Service: Handles conversational AI using hybrid LLM approach - primary local inference with Llama 3.1 8B quantized model, API wrapper fallback for high-demand scenarios.
- Services: auth, user, billing, jobs, reporting (each service is a small, well-scoped container).
- Data stores: PostgreSQL with pgvector (primary relational + vector), Redis (cache/session), object storage (S3-compatible) for blobs.
- Background processing: worker fleet consuming from a durable queue (e.g., Kafka/RabbitMQ).
- Observability: Prometheus (metrics), Grafana (dashboards), ELK/Tempo for logs/traces.

## Data flow (high-level)
1. Client -> API Gateway (TLS, auth)
2. Gateway routes to service; services talk to databases or enqueue background jobs
3. Background workers process jobs and emit events/metrics

## Deployment
- Container images (Docker), Kubernetes for orchestration.
- Infrastructure as code: Terraform for cloud resources.
- CI/CD: build images, run tests, deploy to staging then production via automated pipelines.

## Diagrams
Embed Mermaid diagrams for component and sequence views.

Example component diagram (Mermaid):

```mermaid
graph LR
	Client -->|HTTPS| API[API Gateway]
	API --> Auth[Auth Service]
	API --> Users[User Service]
	Users --> Postgres[(PostgreSQL)]
	Auth --> Redis[(Redis Cache)]
	Jobs[Worker] --> Queue[(Message Queue)]
	Jobs --> S3[(Object Storage)]
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

## Constraints and trade-offs
- Prefers managed cloud services for operational simplicity.
- K8s adds operational overhead but gives scaling and isolation.
- Performance targets: Chat response <1s (warm model), initial model load <30s, memory retrieval <500ms, agent delegation <5s, meditation <10min.
