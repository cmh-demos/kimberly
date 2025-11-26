#!/bin/bash
# K3s Master Node Initialization Script
# This script installs and configures K3s on the master node

set -e

# Wait for cloud-init to complete
cloud-init status --wait

# Update system packages
dnf update -y

# Install required packages
dnf install -y curl wget git iptables

# Disable firewalld (K3s manages iptables directly)
systemctl stop firewalld || true
systemctl disable firewalld || true

# Configure kernel parameters for Kubernetes
cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system

# Load required kernel modules
modprobe br_netfilter
modprobe overlay
echo "br_netfilter" >> /etc/modules-load.d/k8s.conf
echo "overlay" >> /etc/modules-load.d/k8s.conf

# Install K3s server (master)
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${k3s_version}" sh -s - server \
  --token="${k3s_token}" \
  --tls-san="$(curl -s http://169.254.169.254/opc/v1/instance/metadata/publicIp)" \
  --write-kubeconfig-mode=644 \
  --disable=traefik \
  --node-name="${project_name}-master"

# Wait for K3s to be ready
sleep 30
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Create namespaces for Kimberly components
kubectl create namespace kimberly --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Label the namespace
kubectl label namespace kimberly app.kubernetes.io/part-of=kimberly --overwrite

echo "K3s master node initialization complete"
echo "Master node is ready at: $(hostname -I | awk '{print $1}')"
