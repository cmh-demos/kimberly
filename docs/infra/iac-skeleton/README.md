# IaC & local dev skeleton — Kimberly (free-first)

This folder contains a minimal, opinionated scaffold and instructions to bootstrap a free-first development environment and a path toward a production deployment.

Contents:
- `terraform/` — provider-agnostic skeleton and example variables for bootstrapping clusters and managed services.
- `local/` — local development notes using `kind`/`k3d`, Helm charts and quick setup steps.
- `k8s/` — example Kubernetes manifests and CronJob for the nightly meditation job.

Goal: keep the scaffold small and editable, enabling you to iterate in local or free cloud environments (Oracle Always Free or Fly.io) with an easy migration path to managed providers.

See the `terraform/README.md` and `local/k8s-dev.md` for quickstarts.
