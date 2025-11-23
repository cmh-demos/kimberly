# Local Kubernetes development quickstart (free)

This quickstart shows a zero-cost, fast loop for developing Kimberly and Memory Manager locally.

Requirements
- Docker
- `kind` or `k3d` (pick one)
- `kubectl`, `helm`

Steps
1. Create a local cluster:

```bash
# using kind (recommended for integration tests)
kind create cluster --name kimberly-dev

# or using k3d
k3d cluster create kimberly-dev
```

2. Install Postgres (with pgvector) for dev:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install kim-postgres bitnami/postgresql --set postgresqlPassword=example,postgresqlDatabase=kimberly

# If you want pgvector on local Postgres, use a Postgres Docker image or a local extension-enabled chart.
```

3. Install MinIO (S3-compatible object store):

```bash
helm repo add minio https://charts.min.io/
helm install kim-minio minio/minio --set accessKey=myaccesskey,secretKey=mysecretkey
```

4. Install Redis:

```bash
helm install kim-redis bitnami/redis
```

5. Deploy application & memory components
- Build images locally and load into kind/k3d or push to GHCR and deploy via Helm charts or K8s manifests.

6. Nightly meditation (example CronJob): see `../../k8s/meditation-cronjob.yaml` for an example you can adapt.

Tips
- For vector search experiments, run a lightweight FAISS/Milvus/Weaviate container in the cluster.
- Keep secrets in a local .env or use SOPS for safer local secrets handling.
