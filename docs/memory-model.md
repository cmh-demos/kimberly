# Kimberly — AI Memory Model (final)

STATUS: Canonical source of truth for the memory model — EDIT THIS FILE. Owner:
<docs- <team@kimberly.local>> (primary), <infra@kimberly.local> (infra
implementer), <backend@kimberly.local> (code owner) How to regenerate derived
artifacts: run `scripts/refine_memory_model.py` which will produce generated
outputs in `docs/generated/` (do not edit generated files).

**Note**: For discussions and updates, see the Memory Model Wiki Page:

<https://github.com/cmh-demos/kimberly/wiki/Memory-Model>

TL;DR — COST CEILING: FREE. This model enforces a zero-dollar deployment: no
paid managed services, no paid embedding APIs, and defaults that favor local OSS
tooling, lexical-first retrieval, and user-device/offline compute only.
Embeddings are disabled by default and allowed only via self-hosted, local
models (no external paid calls).

1. Executive summary

--------------------

- Memory is split into three tiers: short-term (ephemeral session context),
  long-term
- A nightly scoring process ("meditation") grades memories for retention; low-
  score
- Retrieval uses a hybrid approach: metadata filtering + vector similarity re-
  ranking
- The system is designed for predictable quotas, per-user control, strong
  privacy, and
(persistent personalization), and permanent (canonical facts). items are
archived and eventually removed when quotas are exceeded. for the best context.
auditability.

1. Goals and success criteria (free-by-default)

--------------------

- No monetary cost: avoid any paid APIs, managed services, or hosted vector
  providers.
- Runable on developer or user hardware (laptop / small VPS) using only open-
  source
- Strong metadata/lexical-first retrieval to avoid embeddings where possible;
  optional
components. self-hosted embeddings only when explicitly enabled.

1. Memory tiers and behavior (cost-optimized)

--------------------
All tiers are configurable per-user but offer sane defaults.

- Default quota: 1 MB per user (cost-first default — adjust for heavy users)
-- Short-term (session / ephemeral)
- Default quota: 512 KB per user (aggressively conservative for free-mode)
- Lifetime: ~24 hours (rotated nightly), or until session end
- Purpose: immediate context, conversation state, transient observations
- Access: highest priority for active sessions, cached in Redis for low latency

- Default quota: 10 MB per user (conservative default to reduce persistent
  storage)
-- Long-term (personalization/ongoing state)
- Default quota: 2 MB per user (embed only explicitly-marked high-value items)
- Lifetime: rolling retention that depends on score (weekly baseline)
- Purpose: preferences, habits, project context, frequently useful items
- Access: used during cold-start and background agent reasoning; stored in DB +
  vector
store

- Default quota: 100 MB per user (useful for critical facts but limited to avoid
  high
per-user storage growth)
- Default quota: 10 MB per user (keep permanent storage small; encourage user
export/backup) -- Permanent (canonical/trusted data)
- Lifetime: persistent but subject to rotation when quota is exceeded
- Purpose: canonical facts, credentials (encrypted), user-defined notes
- Access: read-optimized, prioritized for factual responses

1. Data model and versioning

--------------------
Every memory item is a versioned object with lightweight structured metadata to enable evolution of
schema and safe migrations.

MemoryItem (canonical JSON schema)

{ "id": "mem_(uuid)", "user_id": "user_(id)",
  "type": "short-term|long-term|permanent",
"content": "... (stored encrypted if sensitive) ...", "size_bytes": 123,
"metadata": { "tags": ["preference","meeting"],
    "source": "chat|agent|import|upload",
"channels": ["mobile","voice"], "sensitive": false,
    "scope": "private|shared|public",
    "user_feedback": "thumbs_up|thumbs_down|rating:4",
"version": "v1" }, "score": 0.0, "embedding_ref": "vec_(id)", "created_at":
"2025-11-22T10:00:00Z", "last_seen_at": "2025-11-22T10:30:00Z", "audit": {
    "created_by": "system|user|agent",
"consent": true } }

Notes (free-mode):

- Keep content small; avoid storing large files and transcripts by default. If
- Sensitive content: flag metadata.sensitive=true and use local encryption;
  avoid paid
  - Note: ensure retention policies are user-configurable and that consent logs
    are
attachments are required, store them on user devices or local FS; do not use
paid object storage by default. KMS services. recorded for sensitive items.

1. Scoring / meditation (cost-aware operations)

--------------------
The meditation pipeline is the nightly scoring and retention pipeline. Key properties:

- Deterministic & versioned: scoring functions are versioned and produce
  reproducible
scores for the same inputs.
- Auditable: full inputs and outputs stored for debugging and reviews.
- Extensible: scoring components can be combined (rules + ML models).

Recommended baseline scoring formula (interpretable hybrid). Cost changes /
operational notes after this section.

score = normalize( w1 \*relevance_to_goals + w2\* emotional_weight + w3
\*predictive_value + w4\* recency_freq )

Suggested weights (configurable per user/system): w1=0.40, w2=0.30, w3=0.20,
w4=0.10

### Weight Tuning Guide

Tuning scoring weights is challenging because the optimal values depend on
user behavior, use case, and desired memory retention patterns. This section
provides guidance for adjusting weights to match specific needs.

#### Understanding Each Weight Component

| Weight | Component | What It Measures | When to Increase | When to Decrease |
|--------|-----------|------------------|------------------|------------------|
| w1 | relevance_to_goals | How well the memory aligns with user's active goals, projects, and tasks | Task-focused users who want memories tied to current work | Users who value serendipitous or exploratory content |
| w2 | emotional_weight | User sentiment and explicit feedback (thumbs up/down, ratings) | Users who provide frequent feedback; want personalized retention | Users who rarely provide feedback or prefer objective scoring |
| w3 | predictive_value | Historical usefulness (did similar memories lead to helpful actions?) | Power users with established patterns; want predictive assistance | New users or those with changing preferences |
| w4 | recency_freq | How recently and frequently the memory was accessed | Users with fast-changing contexts; want fresh information | Users who value long-term knowledge; archives and references |

#### Configuration Options

Weights can be configured at three levels (in order of precedence):

1. **Per-user config file** (`~/.kimberly/scoring_weights.yaml`):
   ```yaml
   scoring_weights:
     relevance_to_goals: 0.35
     emotional_weight: 0.35
     predictive_value: 0.20
     recency_freq: 0.10
   ```

2. **System config file** (`/etc/kimberly/scoring_weights.yaml`):
   ```yaml
   scoring_weights:
     relevance_to_goals: 0.40
     emotional_weight: 0.30
     predictive_value: 0.20
     recency_freq: 0.10
   ```

3. **Environment variables** (for quick testing):
   ```bash
   export KIMBERLY_WEIGHT_RELEVANCE=0.45
   export KIMBERLY_WEIGHT_EMOTIONAL=0.25
   export KIMBERLY_WEIGHT_PREDICTIVE=0.20
   export KIMBERLY_WEIGHT_RECENCY=0.10
   ```

#### Preset Profiles

For common use cases, use these preset profiles:

| Profile | w1 | w2 | w3 | w4 | Best For |
|---------|-----|-----|-----|-----|----------|
| **balanced** (default) | 0.40 | 0.30 | 0.20 | 0.10 | General use |
| **task-focused** | 0.55 | 0.15 | 0.20 | 0.10 | Project managers, developers |
| **feedback-driven** | 0.25 | 0.50 | 0.15 | 0.10 | Users who rate content |
| **fresh-context** | 0.30 | 0.20 | 0.15 | 0.35 | Fast-paced environments |
| **archival** | 0.45 | 0.25 | 0.25 | 0.05 | Research, long-term knowledge |

To use a preset:
```yaml
scoring_weights:
  preset: task-focused
```

#### Tuning Best Practices

1. **Start with defaults**: Begin with the balanced profile and observe
   memory retention patterns for 1-2 weeks before adjusting.

2. **Make small adjustments**: Change weights by 0.05-0.10 increments.
   Large changes can cause unexpected pruning of important memories.

3. **Ensure weights sum to 1.0**: The system normalizes weights
   automatically, but explicit normalization improves predictability.

4. **Monitor pruning metrics**: After weight changes, check
   `memory.meditation.pruned` metrics to verify the impact.

5. **Test with dry-run**: Use the meditation dry-run mode to preview
   which memories would be pruned before applying changes:
   ```bash
   POST /memory/meditate?dry_run=true
   ```

6. **Document changes**: Keep a log of weight adjustments and their
   observed effects for future reference.

#### Validation Rules

The system enforces these constraints on weight values:
- Each weight must be between 0.0 and 1.0
- All weights must sum to 1.0 (or will be auto-normalized)
- At least one weight must be non-zero

Invalid configurations will fall back to system defaults with a warning.

Component detectors and signals:

- relevance_to_goals: match against active goal models, project tags, and recent
  agent
tasks (0..1)
- emotional_weight: sentiment + explicit user signals (0..1)
- predictive_value: past-match usability (did similar items lead to useful
  actions?)
(0..1)
- recency_freq: frequency and recency normalized (0..1)

Pruning rules (cost-aware):

1. For each tier, compute current_size vs quota.
2. If over quota, sort items by ascending score; move lowest-scoring items into
   an
3. After a configurable grace window (e.g., 30d), items still low-scoring and
   archived
4. Special-case protection: always retain items explicitly marked 'permanent' or
   flagged
'archived-for-grace-period' bucket (retained but excluded from active
retrieval). are deleted permanently (unless user-saved or manually rescued). by
user overrides.

Free-mode specifics:

- Frequency: run meditation rarely (weekly or on-demand) to minimize local
  compute and
- Sampling: only re-score hot/new items; avoid full-dataset scoring unless
  explicitly
- Embeddings: OFF by default. If enabled, embeddings must be generated using
  local/self-
battery use. triggered. hosted OSS models only (no external paid embedding
APIs).

1. Retrieval strategies (minimal cost best-effort)

--------------------
High-quality retrieval is a hybrid of metadata pre-filter + vector similarity re-ranking.

Flow for typical chat context retrieval (cost-aware):

1. Build a metadata filter (tier, tags, time window, sensitivity) to narrow
   candidate
2. For candidates, prefer lexical matching first (SQLite FTS, trigram) or other
   metadata
set. heuristics. If self-hosted embeddings are available they may be used as an
optional re- ranker, but embedding-based search is explicitly opt-in and must be
locally generated.

3. Re-rank by a hybrid score: lambda *semantic_similarity + (1-lambda)*
   memory_score +
freshness_boost. Example: filter candidates by tag="preference" (or other
metadata) and then re-rank the filtered set using cosine similarity over vectors
for top-K relevance.
4. Return top-K for prompt context.

Performance tips (free-mode):

- Prefer in-process caches and local FS-based indexes (SQLite FTS) to avoid
  running
- If embeddings are enabled (self-hosted only), run small CPU-friendly models
  and batch
additional services. processing on local hardware; otherwise rely on lexical
search.
- Use FAISS/Annoy on-disk indices if vector search is necessary and keep vectors
- Always pre-filter with metadata to keep candidate sets tiny before any heavier
  re-
quantized to reduce RAM usage. ranking.

1. Storage & architecture (cheap-by-default stack)

--------------------
Free-mode stack (no paid services):

- SQLite + FTS5 for metadata and text search; run everything on a single machine
- FAISS or Annoy (self-hosted, on-disk) for optional vector search if embeddings
  are
- Avoid managed Redis if possible — use in-process LRU caches; if needed, run a
  tiny
- Local filesystem or user-hosted MinIO for attachments; avoid paid object
  stores.
(developer laptop or small VPS) with no managed services. enabled and produced
locally. local Redis instance.

Component responsibilities (free-mode):

- API service (stateless): defaults to metadata-only writes and never calls paid
embeddings or external APIs. Enforce strict per-user quotas.
- Embedding pipeline: optional; must be self-hosted and invoked explicitly by
- Scoring worker: lightweight, event-driven, or weekly — avoid heavy ML unless
  run
admin/user. No paid embedding provider is allowed. locally by the user.
- Retention worker: run in small batched jobs and use local FS + compact index
- Observability: local-only logs and compressed metrics; do not ship to paid
  analytics
maintenance. services.

1. Privacy, security, and compliance (keep cheap & safe)

--------------------
Design for user control and regulatory compliance.

- Explicit consent for sensitive memory capture and special handling.
- Encryption at rest for all content and attachments; separate key management
  for
sensitive items.
- Per-user controls for purge/forget, export, and consent retraction.
- Audit logs for create/read/delete operations, stored in immutable append-only
  logs.
- Agent access controls: least privilege for agents; agent invocations to memory
  must be
logged.

Cost note: encryption and audit trails add modest storage and CPU overhead. Use
efficient audit schemas + compression for logs to minimize long-term storage
costs.

1. API contract & usage patterns (cost-transparent)

--------------------
Existing endpoints (in OpenAPI):

- POST /memory — create memory (content + metadata) -> returns id, size,
  computed score
- GET /memory — list with filters (type, tags, created_at) + pagination
- DELETE /memory/{id} — delete single memory, with audit log

Recommended additions (now in `docs/openapi.yaml`):

- POST /memory/query — hybrid semantic search + filters
  - Request: { query: string, type?: enum, top_k?: int, filters?: dict }
  - Response: { results: [MemoryItem] }
- POST /memory/meditate — trigger scoring run (useful for debugging / manual
  runs)
  - Response: { status: 'scheduled'|'running'|'complete', processed: n, pruned: m, archived: k }
- GET /memory/metrics — quota usage and last_meditation timestamp

Free-mode API features to implement:

- POST /memory (free-mode): accept metadata + content; embedding_ref must be
  null unless
- POST /memory/embed (optional): accept batch-uploaded embeddings produced
  offline by a
- GET /memory/metrics — expose local resource usage (disk bytes, sqlite index
  size) and
embedding is explicitly enabled with a self-hosted mode. local process (self-
hosted only). embedding-enabled flag; do not include paid-provider metrics.

1. Testing, validation & cost KPIs

--------------------
Focus on correctness, recall, and hallucination reduction.

- Unit tests: schema, scoring logic, quota enforcement
- Integration tests: create -> query -> meditate -> prune
- End-to-end: conversational scenarios where memory should or should not be
  included
- Metric-driven evaluation: recall/precision, false-positive retrievals, rate of
irrelevant memory inclusion in prompts

Add free-mode tests:

- Ensure embedding calls to paid providers are disabled by default and that the
  system
- Validate that the default mode performs lexical search (FTS) and does not
  reach out to
- Confirm quotas and archiving/deletion work as expected within strict free-mode
  limits.
reports embedding provider disabled. external paid services under normal
operations.

1. Operations, budgets & observability

--------------------
Track these operational metrics per user and system-wide:

- memory.items.created, memory.items.deleted, memory.items.archived
- memory.quota.usage.short_term / long_term / permanent
- memory.meditation.last_run, memory.meditation.processed,
  memory.meditation.pruned
- retrieval.latency and retrieval.precision@K

Add these cost-focused observability metrics:

- embedding.calls.total, embedding.calls.failed, embedding.calls.avg_latency
- embedding.budget.remaining_per_user
- vector_index.memory_bytes and vector_index.disk_bytes
- monthly_storage_per_user (estimate)

Set budget alerts: stop embedding ingestion or switch to cheap mode when a user
exceeds their embedding budget; schedule cleanup jobs when per-user storage
exceeds thresholds.

Set alerts for:

- quota usage exceeding thresholds
- large spikes in pruned or deleted items
- memory service errors and embedding failures

1. Low-cost implementation patterns & workflows

--------------------
Creating memory (simplified):

POST /memory payload = {"type": "long-term", "content": "Prefers black coffee",
"metadata": {"tags":["preference"]}} server (low-cost mode):

- accept metadata + content, store metadata and content, but mark
  embedding_ref=null and
- enqueue embedding job in a low-priority queue and batch process embeddings
  during off-
score=0 peak to save compute costs; respond quickly to caller

Querying memory (chat context): client -> create query embedding server ->
filter by user, tier, tag server -> vector search top N server -> re-rank by
hybrid score server -> return top K

Nightly meditation (simplified):

1. For each user: retrieve candidate memory items (all tiers or subset)
2. Compute signals for each (goals match, sentiment, predictive value, recency)
3. Compute score = normalize(weighted sum) and store score
4. If tier over quota: archive lowest scoring items until under quota; mark for
   deletion
after grace period — run pruning in small batches to spread cost.

5. Retention & rotation algorithm (detailed pseudocode, cost controlled)

--------------------
function run_meditation(user_id):
  items = fetch_user_memory(user_id)
  for item in items:
    signals = compute_signals(item)
    item.score = compute_score(signals)
    persist_score(item)

for tier in [short-term, long-term, permanent]: bucket = filter(items, item.tier
== tier and not item.protected) current_size = sum(item.size_bytes for item in
bucket) while current_size > quota[tier]: candidate = min(bucket, key=lambda i:
(i.score, i.created_at)) archive(candidate)   # move to archived state, start
grace window current_size -= candidate.size_bytes

Optimization: apply a daily cap on how much data can be pruned per run to
prevent spikes in I/O and compute.

1. Acceptance criteria (cost targets)

--------------------

- The system implements /memory, /memory/query, /memory/meditate and
  /memory/metrics
- The mediation pipeline runs deterministically and reduces per-user quota
  exceed events
- The retrieval pipeline provides high relevance (measured via user-simulated
  tests) and
according to the OpenAPI changes. to <1% after steady-state. keeps latency
consistent with SLOs

Free targets (strict defaults):

- Average monthly storage per-user (free-default): < 3 MB
- Embedding calls to paid APIs: 0 (no external paid embeddings allowed)
- Vector index memory per 1k users: minimal — prefer on-disk quantized indices
  and <=
200 vectors/user if used

1. Implementation suggestions & low-cost roadmap

--------------------
Phase A (free-only MVP/prototype):

- SQLite + FTS5 for metadata & lexical search. Optional FAISS/Annoy for on-disk
  vector
- Implement free-mode: metadata-first writes; embedding disabled unless self-
  hosted;
- Basic unit & integration tests and a demo that runs entirely on a laptop
  without
search if embeddings are enabled locally. provide a CLI/tool to generate local
embeddings offline if needed. external paid APIs.

Phase B (free scaling):

- Scale using sharded SQLite/Postgres instances and on-disk FAISS/Annoy indices;
- Add per-user caps on vectors, enforced automatically, and auto-disable
  embedding for
continue to avoid paid services. users that exceed caps.

Phase C (cost-mature):

- Add privacy-preserving analytics, advanced audit tooling; keep analytics
  aggregated
and sampled to reduce costs

1. Questions / open decisions

--------------------

- How much user configuration do we expose for scoring weights vs. system
  defaults?
- Do we allow cross-user shared memories or purely per-user? (Current approach
  assumes
single-user scope.)
- How aggressively to archive vs. delete (grace-period length)?
- Consider differential privacy options for aggregated analytics and metrics
  reporting
(avoid exposing sensitive data in aggregated views).

## Appendix: artifacts & repository notes

--------------------

- Iteration artifacts are available at `docs/iterations/` (generated during
  refinement).
- The final source is `docs/memory-model.md` (this file) and the quick OpenAPI
  changes
were added to `docs/openapi.yaml`.

## Memory Cost Guide (practical)

--------------------

### Purpose of guide

Short, targeted guide listing concrete, "free-mode" implementation choices and
practical patterns to run Kimberly without paid services or managed cloud APIs.

### Principles for free-mode

- Avoid paid embedding APIs and managed vector stores.
- Prefer lexical-first retrieval (SQLite FTS, trigram indexes) to avoid
  embeddings
entirely when possible.
- If embeddings are necessary, use small open-source models self-hosted by
- Batch and defer embedding generation to offline/local jobs to avoid high peak
  compute.
- Keep strict per-user limits and prune aggressively to ensure the system can
  run on
developers/users (MiniLM / small sentence-transformers) and run them locally.
Quantize vectors and use on-disk indices to save RAM. commodity hardware without
recurring cloud costs.

### Quick storage math (approximate)

- Vector size estimates per vector:
  - 512 dims *float32 = 512* 4 bytes = 2,048 bytes (~2 KB)
  - 512 dims *float16 = 512* 2 bytes = 1,024 bytes (~1 KB)
  - 512 dims quantized to int8 = 512 bytes (~0.5 KB)

-- Example: per-user storage (free-default)

- Long-term quota = 2 MB user data stored (text+metadata), prefer storing short
structured items
- Avoid embedding most items — embed only small, explicitly-marked items (<= 200
vectors/user)

- Realistic small-case (better): 10 MB content / average memory item 500 bytes
  -> 20k
items, but we should avoid this explosion by storing shorter items and embedding
only important items.

### Simple example with practical limits (free-mode)

Assume per-user: -- Short-term quota: 512 KB (ephemeral) -- Long-term quota: 2
MB content stored, but embed only a small set of high-value items (<= 200
vectors/user) -- Permanent quota: 10 MB for critical facts

With 200 vectors/user * ~1 KB each (fp16 equivalent) = ~200 KB per user for
vectors Add metadata + content stored in SQLite/Postgres (2 MB cap) -> total
~2.2 MB per user on average -> suitable for local deployments.

### Resource footprint (example)

- For 1,000 active users with 200 vectors each (1 KB per vector): ~200 MB
  storage for
- With quantization or int8 you can drop vector storage to ~100 MB. Disk-backed
  index
vectors (disk-backed) keeps RAM low.

### Embedding budget (free-mode)

- Paid embeddings are banned. Default embed budget = 0. Embedding calls to paid
- If embeddings are required, generate them locally using open-source small
  models and
- Provide an opt-in pipeline where admins or power users can run a local
  embedding CLI
providers must never be used in free-mode. limit rate (batch and offline) to
conserve CPU. to populate vector indices.

### Index & retrieval free-mode patterns

- Pre-filter by metadata and rely heavily on lexical search (SQLite FTS or
  trigram) to
- If vector search is used, use on-disk FAISS/Annoy with quantization and cap
  vectors
keep candidate sets very small. per user.
- Prefer per-user small indexes to avoid expensive global quantized indices.

### Free-mode stack recommendations

-- Prototype (free-only): SQLite + FTS5 for text search, FAISS/Annoy on-disk for
   optional vectors, local MinIO or FS for attachments.

- Pros: Runs on a developer laptop or small VPS, no external paid services.
- Cons: Some local CPU usage for embeddings if generated locally; limit
  embedding
operations.

- Scale: Milvus/Weaviate self-hosted with disk-backed indices + PQ/OPQ
  quantization; use
spot/cheap VMs for embedding workers.

### Operational & policy tweaks (free-mode)

- Embeddings OFF by default: store embedding_ref=null unless explicitly enabled
  via
- Provide a local CLI/worker for optional embedding generation; schedule
  embedding tasks
- Enforce strict daily/weekly caps on local embedding runs and per-user vectors
  to stay
self-hosted pipeline. manually or on-demand to keep resource usage under user
control. within resource limits.
- Use compression (gzip) and local lifecycle scripts to age-out old artifacts.

### Testing & validation (free-mode)

- Ensure that default operations do not call any external paid API (embed
  provider
- Simulate local embedding runs and validate that offline pipelines respect per-
  user
- Measure index size and ensure on-disk indices fit within the available disk
  for the
disabled). caps and run-time limits. target deployment.

### Example commands (pgvector) - quick start

1) Create table & vector column

CREATE TABLE memory_items ( id uuid PRIMARY KEY, user_id text, content text,
embedding vector(512), metadata jsonb, created_at timestamptz );

1) Use float16 and compressed storage when available (engine dependent) and set
up periodic VACUUM/REINDEX jobs to maintain index size.

### Next steps (free-mode)

-- Confirm that "cost ceiling = free" means no paid provider usage and I'll lock
   defaults accordingly across the codebase.
-- Implement free-mode enforcement: embedding provider disabled by default, API
   writes default to metadata-only, and CI tests to prevent paid-API calls in
   the free branch.

*This is a short, pragmatic guide. If you want I can: provide a small Python prototype that enacts
the cheap-mode flows, or calculate precise dollar estimates for chosen cloud providers
(AWS/GCP/Azure).*

License and ownership ---------------------

This document is part of the Kimberly project and follows repository license and
contribution rules.
