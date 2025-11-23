#!/usr/bin/env python3
"""Simple cost estimator for memory vectors and storage.
Usage: python3 scripts/cost_smoke_test.py
This prints simple projections given parameters.
"""
import math

# Default parameters (tune per-deployment)
NUM_USERS = 1000
VECTORS_PER_USER = 200
EMBED_DIM = 512
BYTES_PER_DIM_FLOAT32 = 4
BYTES_PER_DIM_FLOAT16 = 2

# Cost assumptions (example)
STORAGE_COST_PER_GB_MONTH = 0.024  # S3 standard approx
VECTOR_STORE_COST_PER_GB_MONTH = (
    0.30  # managed vector store approximate (ignored in free mode)
)
EMBED_COST_PER_CALL = (
    0.0000  # default 0 for free-mode (use provider-specific non-zero when not free)
)


def bytes_for_vectors(num_vectors, dim, per_dim_bytes):
    return num_vectors * dim * per_dim_bytes


def gb(x):
    return x / (1024**3)


def estimate(
    users=NUM_USERS,
    vectors_per_user=VECTORS_PER_USER,
    dim=EMBED_DIM,
    use_float16=True,
    free_mode=True,
    embed_cost_per_call=None,
    vector_store_cost_per_gb=None,
):
    per_dim = BYTES_PER_DIM_FLOAT16 if use_float16 else BYTES_PER_DIM_FLOAT32
    total_vectors = users * vectors_per_user
    total_bytes = bytes_for_vectors(total_vectors, dim, per_dim)
    total_gb = gb(total_bytes)
    if vector_store_cost_per_gb is None:
        vector_store_cost_per_gb = 0.0 if free_mode else VECTOR_STORE_COST_PER_GB_MONTH
    if embed_cost_per_call is None:
        embed_cost_per_call = 0.0 if free_mode else EMBED_COST_PER_CALL

    cost_storage = total_gb * vector_store_cost_per_gb

    # Assuming one embedding per vector
    embedding_calls = total_vectors
    embedding_cost = embedding_calls * embed_cost_per_call

    print(
        f"Users: {users}, vectors/user: {vectors_per_user}, dim: {dim}, float16: {use_float16}"
    )
    print(f"Total vectors: {total_vectors:,}")
    print(f"Total vector storage: {total_bytes:,} bytes ({total_gb:.2f} GB)")
    print(f"Vector storage cost (monthly est): ${cost_storage:.2f}")
    print(f"Embedding calls: {embedding_calls:,} -> cost est: ${embedding_cost:.2f}")
    total_monthly = cost_storage + embedding_cost
    print(f"Total monthly (vectors + embedding calls): ${total_monthly:.2f}")
    return {
        "users": users,
        "vectors_per_user": vectors_per_user,
        "total_vectors": total_vectors,
        "total_bytes": total_bytes,
        "total_gb": total_gb,
        "vector_storage_cost": cost_storage,
        "embedding_calls": embedding_calls,
        "embedding_cost": embedding_cost,
        "total_monthly_cost": total_monthly,
    }


if __name__ == "__main__":
    estimate()
