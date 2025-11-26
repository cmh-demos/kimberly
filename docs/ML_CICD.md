# ML Model CI/CD: Custom Scripts and Tools

This document describes the CI/CD specifics beyond GitHub Actions for ML model testing
and deployment in the Kimberly project.

## Overview

Kimberly uses a hybrid LLM approach with local inference (Llama 3.1 8B quantized) and API
wrapper fallbacks. The ML CI/CD pipeline extends standard GitHub Actions with custom
scripts and tools tailored for ML workloads.

## GitHub Actions Workflows

The repository includes the following GitHub Actions workflows:

| Workflow | File | Purpose |
|----------|------|---------|
| CI | `.github/workflows/ci.yml` | Linting, testing, OpenAPI validation |
| Security | `.github/workflows/security.yml` | Security scans, dependency checks |
| Grooming | `.github/workflows/grooming.yml` | Issue grooming automation |
| Triage | `.github/workflows/copilot-triage.yml` | Issue triage automation |

## Custom Scripts for ML Model Testing

Beyond GitHub Actions, the project uses the following custom scripts:

### 1. Smoke Testing Script

**File:** `scripts/smoke-triage.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
export DRY_RUN=true
python3 scripts/triage_runner.py
```

This script provides a quick smoke test for the triage automation without making live
changes to issues.

### 2. Rules Validation Script

**File:** `scripts/validate_rules.py`

Validates YAML configuration files against embedded JSON schemas. Use for:

- Validating ML model configuration files
- Ensuring schema compliance before deployment
- Pre-commit validation hooks

### 3. Triage Runner

**File:** `scripts/triage_runner.py`

An ML-adjacent automation script that:

- Detects PII in issue content using pattern matching
- Performs duplicate detection using similarity scoring
- Assigns severity and priority using heuristic algorithms
- Supports dry-run mode for safe testing

### 4. Grooming Runner

**File:** `scripts/grooming_runner.py`

Handles post-triage automation with:

- Retry logic with exponential backoff
- Rate limit handling for API calls
- Audit logging with PII sanitization
- GraphQL fallback for assignee operations

## ML Model Testing Recommendations

For ML-specific testing, implement the following:

### Model Validation Tests

```python
# Example test structure for ML model validation
def test_model_response_latency():
    """Chat response should be under 1 second (warm model)."""
    pass

def test_model_load_time():
    """Initial model load should be under 30 seconds."""
    pass

def test_memory_retrieval_latency():
    """Memory retrieval should be under 500ms."""
    pass
```

### Performance Benchmarks

Per `ARCHITECTURE.md`, the following performance targets apply:

| Metric | Target |
|--------|--------|
| Chat response (warm) | < 1 second |
| Initial model load | < 30 seconds |
| Memory retrieval | < 500 ms |
| Agent delegation | < 5 seconds |
| Meditation job | < 10 minutes |

### Bias and Hallucination Testing

Per `CONTRIBUTING.md`, AI-specific tests should include:

- Bias detection tests
- Hallucination checks
- Memory accuracy validation

## ML Model Deployment Pipeline

### Container Build and Registry

Per `ARCHITECTURE.md` and `ADR-0004`:

1. **Registry:** GitHub Container Registry (`ghcr.io`)
2. **Tags:** Use semantic versioning with SHA: `ghcr.io/<org>/kimberly:<semver>-<sha>`
3. **Build:** CI pipelines build, test, sign (optional), and push images

### Deployment Stages

```text
Build → Unit Tests → Integration Tests → Publish Image → Deploy Staging → Smoke Tests → Production
```

### Environment-Specific Deployments

| Environment | Target | Notes |
|-------------|--------|-------|
| Dev | Local k3d/kind | Zero cost, fast iteration |
| Staging | Oracle Always Free / Fly.io | Managed DB, smoke tests |
| Production | Managed K8s (EKS/GKE/AKS) | Multi-AZ, managed vector DB |

## Infrastructure as Code

Model deployment uses Terraform for cloud resources and Kubernetes manifests for
orchestration. Keep configurations provider-agnostic per `ADR-0004`.

### Key Files (Planned)

- `terraform/` — Cloud resource modules
- `k8s/` — Kubernetes manifests and Helm charts
- `docker/` — Dockerfiles for service images

## Observability for ML Workloads

### Metrics to Track

- Model inference latency (p50, p95, p99)
- Memory tier usage per user
- Vector store query latency
- Meditation job duration and success rate

### Monitoring Stack

- **Metrics:** Prometheus + Grafana
- **Logs:** Grafana Loki or ELK
- **Traces:** Tempo

## Recommended ML Testing Tools

Consider integrating these tools for comprehensive ML testing:

| Tool | Purpose |
|------|---------|
| pytest | Unit and integration tests |
| locust | Load testing for API endpoints |
| great-expectations | Data validation |
| mlflow | Model tracking and versioning |
| dvc | Data version control |
| pytest-benchmark | Performance benchmarking |

## Implementation Owners

| Area | Owner |
|------|-------|
| CI/CD Pipeline | DevOps / SRE |
| ML Model Testing | ML Engineer |
| Infrastructure | Infra / SRE |

## Next Steps

1. Implement model validation tests in `tests/`
2. Add performance benchmark tests
3. Create Terraform modules for ML infrastructure
4. Set up MLflow or equivalent for model tracking
5. Add bias/hallucination test suite

## References

- `ARCHITECTURE.md` — System architecture and deployment overview
- `docs/INFRASTRUCTURE.md` — Infrastructure design and operations
- `docs/decisions/ADR-0004.md` — Deployment model decision
- `CONTRIBUTING.md` — Testing strategy and CI requirements
