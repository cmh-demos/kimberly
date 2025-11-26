# Kimberly Infrastructure

This directory contains Infrastructure as Code (IaC) for deploying Kimberly to
Oracle Cloud Always Free tier and production Kubernetes environments.

## Directory Structure

```
infra/
├── terraform/
│   ├── modules/
│   │   └── oracle-always-free/    # OCI Always Free Terraform module
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       ├── outputs.tf
│   │       └── templates/
│   │           ├── k3s-master-init.sh
│   │           └── k3s-worker-init.sh
│   └── environments/
│       ├── production/            # Production environment config
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   ├── outputs.tf
│       │   └── terraform.tfvars.example
│       └── staging/               # Staging environment (placeholder)
├── helm/
│   ├── charts/
│   │   ├── kimberly-api/          # API service Helm chart
│   │   ├── kimberly-memory/       # Memory service Helm chart
│   │   └── kimberly-worker/       # Worker service Helm chart
│   └── values-production.yaml     # Production values overlay
└── README.md
```

## Oracle Cloud Always Free Tier

The Oracle Always Free tier includes:

- **Compute**: Up to 4 Ampere A1 OCPUs and 24 GB memory (ARM-based)
- **Block Storage**: 200 GB total
- **Object Storage**: 10 GB
- **Network**: VCN, load balancers, and egress

Our configuration uses:
- 1 master node (2 OCPU, 12 GB RAM)
- 1 worker node (2 OCPU, 12 GB RAM)
- 100 GB block volume for persistent storage

## Prerequisites

### For Terraform

1. Oracle Cloud account with Always Free eligibility
2. OCI CLI configured with API keys
3. Terraform >= 1.0.0

### For Helm

1. Kubernetes cluster (K3s deployed by Terraform)
2. Helm >= 3.0.0
3. kubectl configured with cluster access

## Quick Start

### 1. Deploy Infrastructure with Terraform

```bash
cd infra/terraform/environments/production

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials

# Initialize and apply
terraform init
terraform plan
terraform apply
```

### 2. Configure kubectl

```bash
# Get the kubeconfig from the master node
ssh opc@<master_public_ip> 'sudo cat /etc/rancher/k3s/k3s.yaml' > ~/.kube/config

# Update the server URL in kubeconfig
sed -i 's/127.0.0.1/<master_public_ip>/g' ~/.kube/config

# Verify connection
kubectl get nodes
```

### 3. Deploy Services with Helm

```bash
cd infra/helm

# Create namespace
kubectl create namespace kimberly

# Create secrets (replace with actual values)
kubectl create secret generic kimberly-db-credentials \
  --from-literal=username=kimberly \
  --from-literal=password=<your-db-password> \
  -n kimberly

kubectl create secret generic kimberly-redis-credentials \
  --from-literal=password=<your-redis-password> \
  -n kimberly

# Install PostgreSQL (with pgvector)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
  -f values-production.yaml \
  -n kimberly

# Install Redis
helm install redis bitnami/redis \
  -f values-production.yaml \
  -n kimberly

# Install Kimberly services
helm install kimberly-api charts/kimberly-api \
  -f values-production.yaml \
  -n kimberly

helm install kimberly-memory charts/kimberly-memory \
  -f values-production.yaml \
  -n kimberly

helm install kimberly-worker charts/kimberly-worker \
  -f values-production.yaml \
  -n kimberly
```

### 4. Set up Ingress and TLS

```bash
# Install ingress-nginx
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx -n kimberly

# Install cert-manager for automatic TLS
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Create Let's Encrypt ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Resource Allocation (Always Free Limits)

| Component | OCPUs | Memory | Storage |
|-----------|-------|--------|---------|
| K3s Master | 2 | 12 GB | 50 GB boot |
| K3s Worker | 2 | 12 GB | 50 GB boot |
| Data Volume | - | - | 100 GB |
| **Total** | **4** | **24 GB** | **200 GB** |

## Security Considerations

1. **SSH Access**: Restrict `ssh_allowed_cidr` to your IP address
2. **Secrets**: Use Kubernetes secrets or external secret managers
3. **TLS**: Enable cert-manager for automatic certificate management
4. **Network**: Private subnet for internal services
5. **RBAC**: Service accounts with minimal permissions

## Monitoring

The Helm charts include Prometheus annotations for metrics scraping.
Add Prometheus and Grafana for observability:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

## Troubleshooting

### Terraform Issues

```bash
# Check OCI connectivity
oci iam region list

# Debug Terraform
TF_LOG=DEBUG terraform plan
```

### Kubernetes Issues

```bash
# Check node status
kubectl get nodes -o wide

# Check pod status
kubectl get pods -n kimberly

# View logs
kubectl logs -n kimberly deployment/kimberly-api
```

### K3s Issues

```bash
# On master node
sudo systemctl status k3s
sudo journalctl -u k3s -f

# On worker node
sudo systemctl status k3s-agent
sudo journalctl -u k3s-agent -f
```

## References

- [Oracle Cloud Always Free](https://www.oracle.com/cloud/free/)
- [K3s Documentation](https://docs.k3s.io/)
- [Helm Documentation](https://helm.sh/docs/)
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
