# Terraform skeleton — provider-agnostic

This directory contains a small Terraform skeleton and examples that show how to structure modules for cluster, database, storage, and the memory manager.

Important notes:
- The `main.tf` file here is intentionally a placeholder / opinionated layout to be completed for your chosen provider (Oracle Cloud, AWS, GCP, Azure). It tries to avoid early provider lock-in.
- For early proof-of-concept use `local` or `null_resource` + `local-exec` to bootstrap a small k3s/k0s cluster on free VMs (Oracle Always Free) or deploy to Fly.io.

Suggested workflow:
1. Pick target provider (local -> Oracle Always Free or Fly.io for free-first).  
2. Update `terraform.tfvars` with provider credentials and region.  
3. Run `terraform init` → `terraform plan` → `terraform apply` to provision.

Local dev and k8s manifests are easier and faster for initial work — see `../local/k8s-dev.md`.
