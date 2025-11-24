# Kimberly — Free-Mode Runbook

## Purpose

This runbook explains how to deploy and run the Kimberly memory stack without incurring paid service costs: fully self-hosted, local-first, and embedding-free by default.

## Key principles

- Avoid any paid API (embedding or vector provider).
- Default to metadata-first and lexical search (SQLite FTS) for retrieval.
- Optional embeddings must be self-hosted with open-source models and executed on local hardware.
- Keep per-user quotas small and enforce strict retention.

## Quick setup (developer laptop)

Prerequisites: Python 3.10+, Git, local OS package manager.

1. Clone repo & create venv

```bash
git clone <repo>
cd kimberly
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt  # add requirements if missing
```

1. Minimal stack for free operation

- SQLite (included in Python stdlib via sqlite3)
- Optionally: FAISS (pip install faiss-cpu) for local on-disk vectors
- Optional local MinIO for attachments, or just use the filesystem

1. Example initial data & run

```bash
python3 scripts/cost_smoke_test.py  # quick resource-check example
# The web API / app code (if present) should start with embedding disabled.

# Start the demo server or run the integration harness per README.

```

## Optional: local embedding pipeline (self-hosted)

If you need embeddings and want to remain free-of-paid-APIs, you can run a tiny local model on CPU. Example options:

- sentence-transformers (MiniLM) - CPU friendly for small batches
  - pip install -U sentence-transformers
  - Create a small script to run batches and write embeddings to disk
- faiss-cpu for on-disk approx search

Example simple pipeline:

```bash
python3 -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('all-MiniLM-L6-v2'); print(m.encode(['hello world']))"
# Use a small batch script to produce embeddings and upload with POST /memory/embed (self-hosted endpoint only)

```

## Enforcing free-mode in development / CI

- Make embedding provider disabled by default in the config (e.g. EMBEDDING_PROVIDER=None).
- Add tests to prevent PRs from enabling paid providers without review.
  - The lighthouse test: ensure estimate(..., free_mode=True) returns zero embedding costs.
- Add a CI policy to fail the build if new code references typical paid providers (simple grep for "openai|pinecone|replicate|cohere" in the changed files).

## Monitoring & operational suggestions

- Track per-user storage (disk), on-disk index size, and local CPU usage.
- Enforce quotas strictly: refuse writes or auto-archive when quota exceeded.
- Provide a local UI/CLI to trigger offline embedding jobs and to export user data.

## Tradeoffs & limitations

- Lower recall and semantic power without embeddings: expect lexical search to be less powerful for paraphrase retrieval.
- Local embedding generation on CPU is slower and limited; expensive or complex embedding workflows are intentionally disallowed in free-mode.
- Free deployments are great for single-user, dev, or small teams. For large scale and high performance you will need resources (paid services or supported self-hosted infra).

## Next steps

- Implement a simple CLI to generate and upload embeddings locally (optional), plus a demo script for the free-mode API.
- Add CI grep rules to prevent accidental introduction of paid providers.

If you'd like, I can:

- Implement the free-mode CLI embeddings generator and demo (all-local), or
- Add CI rules to block external provider usage and add a few end-to-end tests that cover free-mode workflows.
