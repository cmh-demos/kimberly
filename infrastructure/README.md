# Infrastructure

This directory contains infrastructure-as-code for deploying Kimberly.

## Directory Structure

```text
infrastructure/
└── helm/
    └── monitoring/     # Prometheus, Grafana, Loki, Tempo stack
```

## Helm Charts

### Monitoring Stack

The monitoring chart deploys the complete observability stack:

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Dashboards and visualization
- **Alertmanager** - Alert routing and notification
- **Loki** - Log aggregation
- **Tempo** - Distributed tracing

See [helm/monitoring/README.md](helm/monitoring/README.md) for details.

## Quick Start

### Prerequisites

- Kubernetes cluster (local: kind/k3d, cloud: EKS/GKE/AKS)
- Helm 3.x installed
- kubectl configured for your cluster

### Deploy monitoring stack

```bash
# Add Helm repositories
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace monitoring

# Deploy monitoring
cd helm/monitoring
helm dependency update
helm install kimberly-monitoring . \
  --namespace monitoring \
  --set kube-prometheus-stack.grafana.adminPassword=changeme
```

## Environments

| Environment | Description | Recommended Setup |
|-------------|-------------|-------------------|
| Local Dev | Development and testing | kind/k3d cluster |
| Staging | Pre-production testing | Small managed K8s or Fly.io |
| Production | Live workloads | Managed K8s (EKS/GKE/AKS) |

## References

- [Kimberly Architecture](../ARCHITECTURE.md)
- [Infrastructure Design](../docs/INFRASTRUCTURE.md)
- [ADR-0004: Deployment Model](../docs/decisions/ADR-0004.md)
