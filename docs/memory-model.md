# Kimberly — AI Memory Model (final)

STATUS: Canonical source of truth for the memory model — EDIT THIS FILE.
Owner: docs-team@kimberly.local (primary), infra@kimberly.local (infra implementer), backend@kimberly.local (code owner)
How to regenerate derived artifacts: run `scripts/refine_memory_model.py` which will produce generated outputs in `docs/generated/` (do not edit generated files).

**Note**: For discussions and updates, see the [Memory Model Wiki Page](https://github.com/cmh-demos/kimberly/wiki/Memory-Model).

TL;DR — COST CEILING: FREE. This model enforces a zero-dollar deployment: no paid managed services, no paid embedding APIs, and defaults that favor local OSS tooling, lexical-first retrieval, and user-device/offline compute only. Embeddings are disabled by default and allowed only via self-hosted, local models (no external paid calls).

1. Executive summary
--------------------
- Memory is split into three tiers: short-term (ephemeral session context), long-term (persistent personalization), and permanent (canonical facts).
- A nightly scoring process ("meditation") grades memories for retention; low-score items are archived and eventually removed when quotas are exceeded.
- Retrieval uses a hybrid approach: metadata filtering + vector similarity re-ranking for the best context.
- The system is designed for predictable quotas, per-user control, strong privacy, and auditability.

2. Goals and success criteria (free-by-default)
-----------------------------
- No monetary cost: avoid any paid APIs, managed services, or hosted vector providers.
- Runable on developer or user hardware (laptop / small VPS) using only open-source components.
- Strong metadata/lexical-first retrieval to avoid embeddings where possible; optional self-hosted embeddings only when explicitly enabled.

3. Memory tiers and behavior (cost-optimized)
---------------------------
All tiers are configurable per-user but offer sane defaults.

  - Default quota: 1 MB per user (cost-first default — adjust for heavy users)
-- Short-term (session / ephemeral)
  - Default quota: 512 KB per user (aggressively conservative for free-mode)
  - Lifetime: ~24 hours (rotated nightly), or until session end
  - Purpose: immediate context, conversation state, transient observations
  - Access: highest priority for active sessions, cached in Redis for low latency

  - Default quota: 10 MB per user (conservative default to reduce persistent storage)
-- Long-term (personalization/ongoing state)
  - Default quota: 2 MB per user (embed only explicitly-marked high-value items)
  - Lifetime: rolling retention that depends on score (weekly baseline)
  - Purpose: preferences, habits, project context, frequently useful items
  - Access: used during cold-start and background agent reasoning; stored in DB + vector store

  - Default quota: 100 MB per user (useful for critical facts but limited to avoid high per-user storage growth)
-- Permanent (canonical/trusted data)
  - Default quota: 10 MB per user (keep permanent storage small; encourage user export/backup)
  - Lifetime: persistent but subject to rotation when quota is exceeded
  - Purpose: canonical facts, credentials (encrypted), user-defined notes
  - Access: read-optimized, prioritized for factual responses

4. Data model and versioning
---------------------------
Every memory item is a versioned object with lightweight structured metadata to enable evolution of schema and safe migrations.

MemoryItem (canonical JSON schema)

{
  "id": "mem_<uuid>",
  "user_id": "user_<id>",
  "type": "short-term|long-term|permanent",
  "content": "... (stored encrypted if sensitive) ...",
  "size_bytes": 123,
  "metadata": {
    "tags": ["preference","meeting"],
    "source": "chat|agent|import|upload",
    "channels": ["mobile","voice"],
    "sensitive": false,
    "scope": "private|shared|public",
    "user_feedback": "thumbs_up|thumbs_down|rating:4",
    "version": "v1"
  },
  "score": 0.0,
  "embedding_ref": "vec_<id>",
  "created_at": "2025-11-22T10:00:00Z",
  "last_seen_at": "2025-11-22T10:30:00Z",
  "audit": {
    "created_by": "system|user|agent",
    "consent": true
  }
}

Notes (free-mode):
- Keep content small; avoid storing large files and transcripts by default. If attachments are required, store them on user devices or local FS; do not use paid object storage by default.
- Sensitive content: flag metadata.sensitive=true and use local encryption; avoid paid KMS services.
  - Note: ensure retention policies are user-configurable and that consent logs are recorded for sensitive items.

5. Scoring / meditation (cost-aware operations)
-----------------------------------------------
The meditation pipeline is the nightly scoring and retention pipeline. Key properties:

- Deterministic & versioned: scoring functions are versioned and produce reproducible scores for the same inputs.
- Auditable: full inputs and outputs stored for debugging and reviews.
- Extensible: scoring components can be combined (rules + ML models).

Recommended baseline scoring formula (interpretable hybrid). Cost changes / operational notes after this section.

score = normalize( w1 * relevance_to_goals + w2 * emotional_weight + w3 * predictive_value + w4 * recency_freq )

Suggested weights (configurable per user/system): w1=0.40, w2=0.30, w3=0.20, w4=0.10

Component detectors and signals:
- relevance_to_goals: match against active goal models, project tags, and recent agent tasks (0..1)
- emotional_weight: sentiment + explicit user signals (0..1)
- predictive_value: past-match usability (did similar items lead to useful actions?) (0..1)
- recency_freq: frequency and recency normalized (0..1)

Pruning rules (cost-aware):
1. For each tier, compute current_size vs quota.
2. If over quota, sort items by ascending score; move lowest-scoring items into an 'archived-for-grace-period' bucket (retained but excluded from active retrieval).
3. After a configurable grace window (e.g., 30d), items still low-scoring and archived are deleted permanently (unless user-saved or manually rescued).
4. Special-case protection: always retain items explicitly marked 'permanent' or flagged by user overrides.

Free-mode specifics:
- Frequency: run meditation rarely (weekly or on-demand) to minimize local compute and battery use.
- Sampling: only re-score hot/new items; avoid full-dataset scoring unless explicitly triggered.
- Embeddings: OFF by default. If enabled, embeddings must be generated using local/self-hosted OSS models only (no external paid embedding APIs).

6. Retrieval strategies (minimal cost best-effort)
------------------------------------------------
High-quality retrieval is a hybrid of metadata pre-filter + vector similarity re-ranking.

Flow for typical chat context retrieval (cost-aware):
1. Build a metadata filter (tier, tags, time window, sensitivity) to narrow candidate set.
2. For candidates, prefer lexical matching first (SQLite FTS, trigram) or other metadata heuristics. If self-hosted embeddings are available they may be used as an optional re-ranker, but embedding-based search is explicitly opt-in and must be locally generated.
    
  Example: filter candidates by tag="preference" (or other metadata) and then re-rank the filtered set using cosine similarity over vectors for top-K relevance.
3. Re-rank by a hybrid score: lambda * semantic_similarity + (1-lambda) * memory_score + freshness_boost.
4. Return top-K for prompt context.

Performance tips (free-mode):
- Prefer in-process caches and local FS-based indexes (SQLite FTS) to avoid running additional services.
- If embeddings are enabled (self-hosted only), run small CPU-friendly models and batch processing on local hardware; otherwise rely on lexical search.
- Use FAISS/Annoy on-disk indices if vector search is necessary and keep vectors quantized to reduce RAM usage.
- Always pre-filter with metadata to keep candidate sets tiny before any heavier re-ranking.

7. Storage & architecture (cheap-by-default stack)
-------------------------------------------
Free-mode stack (no paid services):
- SQLite + FTS5 for metadata and text search; run everything on a single machine (developer laptop or small VPS) with no managed services.
- FAISS or Annoy (self-hosted, on-disk) for optional vector search if embeddings are enabled and produced locally.
- Avoid managed Redis if possible — use in-process LRU caches; if needed, run a tiny local Redis instance.
- Local filesystem or user-hosted MinIO for attachments; avoid paid object stores.

Component responsibilities (free-mode):
- API service (stateless): defaults to metadata-only writes and never calls paid embeddings or external APIs. Enforce strict per-user quotas.
- Embedding pipeline: optional; must be self-hosted and invoked explicitly by admin/user. No paid embedding provider is allowed.
- Scoring worker: lightweight, event-driven, or weekly — avoid heavy ML unless run locally by the user.
- Retention worker: run in small batched jobs and use local FS + compact index maintenance.
- Observability: local-only logs and compressed metrics; do not ship to paid analytics services.

8. Privacy, security, and compliance (keep cheap & safe)
-----------------------------------
Design for user control and regulatory compliance.

- Explicit consent for sensitive memory capture and special handling.
- Encryption at rest for all content and attachments; separate key management for sensitive items.
- Per-user controls for purge/forget, export, and consent retraction.
- Audit logs for create/read/delete operations, stored in immutable append-only logs.
- Agent access controls: least privilege for agents; agent invocations to memory must be logged.

Cost note: encryption and audit trails add modest storage and CPU overhead. Use efficient audit schemas + compression for logs to minimize long-term storage costs.

9. API contract & usage patterns (cost-transparent)
--------------------------------
Existing endpoints (in OpenAPI):
- POST /memory — create memory (content + metadata) -> returns id, size, computed score
- GET /memory — list with filters (type, tags, created_at) + pagination
- DELETE /memory/{id} — delete single memory, with audit log

Recommended additions (now in `docs/openapi.yaml`):
- POST /memory/query — hybrid semantic search + filters
  - Request: { query: string, type?: enum, top_k?: int, filters?: dict }
  - Response: { results: [MemoryItem] }
- POST /memory/meditate — trigger scoring run (useful for debugging / manual runs)
  - Response: { status: 'scheduled'|'running'|'complete', processed: n, pruned: m, archived: k }
- GET /memory/metrics — quota usage and last_meditation timestamp

Free-mode API features to implement:
- POST /memory (free-mode): accept metadata + content; embedding_ref must be null unless embedding is explicitly enabled with a self-hosted mode.
- POST /memory/embed (optional): accept batch-uploaded embeddings produced offline by a local process (self-hosted only).
- GET /memory/metrics — expose local resource usage (disk bytes, sqlite index size) and embedding-enabled flag; do not include paid-provider metrics.

10. Testing, validation & cost KPIs
-------------------------------
Focus on correctness, recall, and hallucination reduction.

- Unit tests: schema, scoring logic, quota enforcement
- Integration tests: create -> query -> meditate -> prune
- End-to-end: conversational scenarios where memory should or should not be included
- Metric-driven evaluation: recall/precision, false-positive retrievals, rate of irrelevant memory inclusion in prompts

Add free-mode tests:
- Ensure embedding calls to paid providers are disabled by default and that the system reports embedding provider disabled.
- Validate that the default mode performs lexical search (FTS) and does not reach out to external paid services under normal operations.
- Confirm quotas and archiving/deletion work as expected within strict free-mode limits.

11. Operations, budgets & observability
-----------------------------
Track these operational metrics per user and system-wide:
- memory.items.created, memory.items.deleted, memory.items.archived
- memory.quota.usage.short_term / long_term / permanent
- memory.meditation.last_run, memory.meditation.processed, memory.meditation.pruned
- retrieval.latency and retrieval.precision@K

Add these cost-focused observability metrics:
- embedding.calls.total, embedding.calls.failed, embedding.calls.avg_latency
- embedding.budget.remaining_per_user
- vector_index.memory_bytes and vector_index.disk_bytes
- monthly_storage_per_user (estimate)

Set budget alerts: stop embedding ingestion or switch to cheap mode when a user exceeds their embedding budget; schedule cleanup jobs when per-user storage exceeds thresholds.

Set alerts for:
- quota usage exceeding thresholds
- large spikes in pruned or deleted items
- memory service errors and embedding failures

12. Low-cost implementation patterns & workflows
---------------------------------
Creating memory (simplified):

POST /memory
payload = {"type": "long-term", "content": "Prefers black coffee", "metadata": {"tags":["preference"]}}
server (low-cost mode):
  - accept metadata + content, store metadata and content, but mark embedding_ref=null and score=0
  - enqueue embedding job in a low-priority queue and batch process embeddings during off-peak to save compute costs; respond quickly to caller

Querying memory (chat context):
client -> create query embedding
server -> filter by user, tier, tag
server -> vector search top N
server -> re-rank by hybrid score
server -> return top K

Nightly meditation (simplified):
1. For each user: retrieve candidate memory items (all tiers or subset)
2. Compute signals for each (goals match, sentiment, predictive value, recency)
3. Compute score = normalize(weighted sum) and store score
4. If tier over quota: archive lowest scoring items until under quota; mark for deletion after grace period — run pruning in small batches to spread cost.

13. Retention & rotation algorithm (detailed pseudocode, cost controlled)
----------------------------------------------------
function run_meditation(user_id):
  items = fetch_user_memory(user_id)
  for item in items:
    signals = compute_signals(item)
    item.score = compute_score(signals)
    persist_score(item)

  for tier in [short-term, long-term, permanent]:
    bucket = filter(items, item.tier == tier and not item.protected)
    current_size = sum(item.size_bytes for item in bucket)
    while current_size > quota[tier]:
      candidate = min(bucket, key=lambda i: (i.score, i.created_at))
      archive(candidate)   # move to archived state, start grace window
      current_size -= candidate.size_bytes

    Optimization: apply a daily cap on how much data can be pruned per run to prevent spikes in I/O and compute.

14. Acceptance criteria (cost targets)
-----------------------
- The system implements /memory, /memory/query, /memory/meditate and /memory/metrics according to the OpenAPI changes.
- The mediation pipeline runs deterministically and reduces per-user quota exceed events to <1% after steady-state.
- The retrieval pipeline provides high relevance (measured via user-simulated tests) and keeps latency consistent with SLOs

Free targets (strict defaults):
- Average monthly storage per-user (free-default): < 3 MB
- Embedding calls to paid APIs: 0 (no external paid embeddings allowed)
- Vector index memory per 1k users: minimal — prefer on-disk quantized indices and <= 200 vectors/user if used

15. Implementation suggestions & low-cost roadmap
--------------------------------------
Phase A (free-only MVP/prototype):
- SQLite + FTS5 for metadata & lexical search. Optional FAISS/Annoy for on-disk vector search if embeddings are enabled locally.
- Implement free-mode: metadata-first writes; embedding disabled unless self-hosted; provide a CLI/tool to generate local embeddings offline if needed.
- Basic unit & integration tests and a demo that runs entirely on a laptop without external paid APIs.

Phase B (free scaling):
- Scale using sharded SQLite/Postgres instances and on-disk FAISS/Annoy indices; continue to avoid paid services.
- Add per-user caps on vectors, enforced automatically, and auto-disable embedding for users that exceed caps.

Phase C (cost-mature):
- Add privacy-preserving analytics, advanced audit tooling; keep analytics aggregated and sampled to reduce costs

16. Questions / open decisions
----------------------------
- How much user configuration do we expose for scoring weights vs. system defaults?
- Do we allow cross-user shared memories or purely per-user? (Current approach assumes single-user scope.)
- How aggressively to archive vs. delete (grace-period length)?
 - Consider differential privacy options for aggregated analytics and metrics reporting (avoid exposing sensitive data in aggregated views).

Appendix: artifacts & repository notes
-------------------------------------
- Iteration artifacts are available at `docs/iterations/` (generated during refinement).
- The final source is `docs/memory-model.md` (this file) and the quick OpenAPI changes were added to `docs/openapi.yaml`.

License and ownership
---------------------
This document is part of the Kimberly project and follows repository license and contribution rules.
