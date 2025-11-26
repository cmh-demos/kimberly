#!/bin/bash
# K3s Worker Node Initialization Script
# This script installs and configures K3s on worker nodes

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

# Wait for master node to be ready (retry logic)
MASTER_IP="${master_ip}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if curl -sf -o /dev/null "https://$MASTER_IP:6443" --insecure; then
    echo "Master node is reachable"
    break
  fi
  echo "Waiting for master node... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 30
  RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "Failed to reach master node after $MAX_RETRIES attempts"
  exit 1
fi

# Install K3s agent (worker)
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${k3s_version}" sh -s - agent \
  --server="https://$MASTER_IP:6443" \
  --token="${k3s_token}"

echo "K3s worker node initialization complete"
echo "Worker node joined cluster at: $MASTER_IP"
