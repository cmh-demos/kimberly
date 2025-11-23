# Kimberly — Memory Cost Guide (practical)

Purpose
-------
Short, targeted guide listing concrete, "free-mode" implementation choices and practical patterns to run Kimberly without paid services or managed cloud APIs.

Principles for free-mode
--------------------------
- Avoid paid embedding APIs and managed vector stores.
- Prefer lexical-first retrieval (SQLite FTS, trigram indexes) to avoid embeddings entirely when possible.
- If embeddings are necessary, use small open-source models self-hosted by developers/users (MiniLM / small sentence-transformers) and run them locally.
- Batch and defer embedding generation to offline/local jobs to avoid high peak compute. Quantize vectors and use on-disk indices to save RAM.
- Keep strict per-user limits and prune aggressively to ensure the system can run on commodity hardware without recurring cloud costs.

Quick storage math (approximate)
-------------------------------
- Vector size estimates per vector:
  - 512 dims * float32 = 512 * 4 bytes = 2,048 bytes (~2 KB)
  - 512 dims * float16 = 512 * 2 bytes = 1,024 bytes (~1 KB)
  - 512 dims quantized to int8 = 512 bytes (~0.5 KB)

-- Example: per-user storage (free-default)
  - Long-term quota = 2 MB user data stored (text+metadata), prefer storing short structured items
  - Avoid embedding most items — embed only small, explicitly-marked items (<= 200 vectors/user)

- Realistic small-case (better): 10 MB content / average memory item 500 bytes -> 20k items, but we should avoid this explosion by storing shorter items and embedding only important items.

Simple example with practical limits (free-mode)
-----------------------------------
Assume per-user:
-- Short-term quota: 512 KB (ephemeral)
-- Long-term quota: 2 MB content stored, but embed only a small set of high-value items (<= 200 vectors/user)
-- Permanent quota: 10 MB for critical facts

With 200 vectors/user * ~1 KB each (fp16 equivalent) = ~200 KB per user for vectors
Add metadata + content stored in SQLite/Postgres (2 MB cap) -> total ~2.2 MB per user on average -> suitable for local deployments.

Resource footprint (example):
- For 1,000 active users with 200 vectors each (1 KB per vector): ~200 MB storage for vectors (disk-backed)
- With quantization or int8 you can drop vector storage to ~100 MB. Disk-backed index keeps RAM low.

Embedding budget (free-mode)
----------------
- Paid embeddings are banned. Default embed budget = 0. Embedding calls to paid providers must never be used in free-mode.
- If embeddings are required, generate them locally using open-source small models and limit rate (batch and offline) to conserve CPU.
- Provide an opt-in pipeline where admins or power users can run a local embedding CLI to populate vector indices.

Index & retrieval free-mode patterns
-------------------------------------
- Pre-filter by metadata and rely heavily on lexical search (SQLite FTS or trigram) to keep candidate sets very small.
- If vector search is used, use on-disk FAISS/Annoy with quantization and cap vectors per user.
- Prefer per-user small indexes to avoid expensive global quantized indices.

Free-mode stack recommendations
--------------------------
-- Prototype (free-only): SQLite + FTS5 for text search, FAISS/Annoy on-disk for optional vectors, local MinIO or FS for attachments.
  - Pros: Runs on a developer laptop or small VPS, no external paid services.
  - Cons: Some local CPU usage for embeddings if generated locally; limit embedding operations.

- Scale: Milvus/Weaviate self-hosted with disk-backed indices + PQ/OPQ quantization; use spot/cheap VMs for embedding workers.

Operational & policy tweaks (free-mode)
---------------------------
 - Embeddings OFF by default: store embedding_ref=null unless explicitly enabled via self-hosted pipeline.
 - Provide a local CLI/worker for optional embedding generation; schedule embedding tasks manually or on-demand to keep resource usage under user control.
 - Enforce strict daily/weekly caps on local embedding runs and per-user vectors to stay within resource limits.
 - Use compression (gzip) and local lifecycle scripts to age-out old artifacts.

Testing & validation (free-mode)
--------------------
 - Ensure that default operations do not call any external paid API (embed provider disabled).
 - Simulate local embedding runs and validate that offline pipelines respect per-user caps and run-time limits.
 - Measure index size and ensure on-disk indices fit within the available disk for the target deployment.

Example commands (pgvector) - quick start
----------------------------------------
1) Create table & vector column

  CREATE TABLE memory_items (
    id uuid PRIMARY KEY,
    user_id text,
    content text,
    embedding vector(512),
    metadata jsonb,
    created_at timestamptz
  );

2) Use float16 and compressed storage when available (engine dependent) and set up periodic VACUUM/REINDEX jobs to maintain index size.

Next steps (free-mode):
-- Confirm that "cost ceiling = free" means no paid provider usage and I'll lock defaults accordingly across the codebase.
-- Implement free-mode enforcement: embedding provider disabled by default, API writes default to metadata-only, and CI tests to prevent paid-API calls in the free branch.


*This is a short, pragmatic guide. If you want I can: provide a small Python prototype that enacts the cheap-mode flows, or calculate precise dollar estimates for chosen cloud providers (AWS/GCP/Azure).*