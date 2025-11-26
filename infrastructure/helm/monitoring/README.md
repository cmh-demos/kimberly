# Kimberly Monitoring Stack

This Helm chart deploys the complete observability stack for Kimberly,
including metrics, logging, and tracing.

## Components

| Component | Description | Default |
|-----------|-------------|---------|
| **kube-prometheus-stack** | Prometheus, Grafana, and Alertmanager | Enabled |
| **Loki** | Log aggregation | Enabled |
| **Tempo** | Distributed tracing | Enabled |

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Sufficient cluster resources (see [Resource Requirements](#resource-requirements))

## Installation

### Add required Helm repositories

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Install the chart

```bash
# Create namespace
kubectl create namespace monitoring

# Update dependencies
cd infrastructure/helm/monitoring
helm dependency update

# Install with default values (development/local)
helm install kimberly-monitoring . \
  --namespace monitoring \
  --set kube-prometheus-stack.grafana.adminPassword=<your-password>

# Install with production values
helm install kimberly-monitoring . \
  --namespace monitoring \
  -f values-production.yaml \
  --set kube-prometheus-stack.grafana.adminPassword=<your-password>
```

## Configuration

### Key configuration options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prometheus.enabled` | Enable Prometheus stack | `true` |
| `loki.enabled` | Enable Loki | `true` |
| `tempo.enabled` | Enable Tempo | `true` |

See [values.yaml](values.yaml) for all configuration options.

### Accessing Grafana

```bash
# Port forward to Grafana
kubectl port-forward svc/kimberly-monitoring-grafana 3000:80 \
  -n monitoring

# Access at http://localhost:3000
# Default username: admin
```

### Kimberly-specific alerts

The chart includes custom PrometheusRules for Kimberly:

- **MeditationJobFailed** - Alerts when meditation jobs fail
- **MeditationJobHighLatency** - Alerts when meditation runs > 10 minutes
- **PostgresStorageWarning/Critical** - Storage usage alerts at 80%/90%
- **QueueBacklogHigh** - Message queue backlog alerts
- **APIHighErrorRate** - API 5xx rate > 5%
- **APIHighLatency** - API p95 latency > 1s
- **MemoryTierQuotaExceeded** - Memory quota violations
- **VectorSearchHighLatency** - Vector search p99 > 500ms
- **BackupJobFailed** - Backup job failures

### Kimberly dashboard

A pre-configured Grafana dashboard is included with panels for:

- Request rate by service
- Request latency (p95)
- Error rate by service
- Memory items by tier
- Vector search latency
- Meditation items pruned

## Resource requirements

### Development (default values)

| Component | CPU Request | Memory Request |
|-----------|-------------|----------------|
| Prometheus | 200m | 400Mi |
| Alertmanager | 50m | 100Mi |
| Loki | 100m | 256Mi |
| Tempo | 100m | 256Mi |

### Production (values-production.yaml)

| Component | CPU Request | Memory Request |
|-----------|-------------|----------------|
| Prometheus (x2) | 500m | 1Gi |
| Alertmanager (x2) | 100m | 200Mi |
| Loki (scalable) | varies | varies |
| Tempo | 250m | 512Mi |

## Upgrade

```bash
helm upgrade kimberly-monitoring . \
  --namespace monitoring \
  -f values-production.yaml
```

## Uninstall

```bash
helm uninstall kimberly-monitoring --namespace monitoring
```

## Troubleshooting

### Check component status

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### View Prometheus targets

```bash
kubectl port-forward svc/kimberly-monitoring-prometheus 9090:9090 \
  -n monitoring
# Access http://localhost:9090/targets
```

### View Alertmanager

```bash
kubectl port-forward svc/kimberly-monitoring-alertmanager 9093:9093 \
  -n monitoring
# Access http://localhost:9093
```

## References

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Loki](https://grafana.com/docs/loki/latest/)
- [Tempo](https://grafana.com/docs/tempo/latest/)
- [Kimberly Infrastructure](../../docs/INFRASTRUCTURE.md)
