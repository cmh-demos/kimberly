# Deployment appendix — free-hosting choices and portability

This appendix summarizes recommended bootstrap options, portability guidance, and local development tips.

Bootstrap provider options (short)
- Oracle Cloud Always Free — self-managed VMs (run k3s/k0s): pros — predictable free tier, full control; cons — more ops work (maintenance, upgrades).
- Fly.io — managed app platform (simpler deployments): pros — fast setup, minimal infra; cons — not full-featured K8s, potential limits when scaling.

Portability & migration guardrails
- Keep Terraform, manifests, and Helm charts provider-agnostic where possible.
- Rely on S3-compatible object storage, PostgreSQL, and Redis that can be swapped between providers.
- Use `ghcr.io` (GitHub Container Registry) for images to avoid cloud-specific registries.

Local development tips
- Use `kind` or `k3d` for local Kubernetes clusters and `docker`/`podman` for builds.
- Keep secrets in local dev env files or use a local secrets manager (eg. `sops` with a test key).

When to consider multi-provider
- Consider adding a second provider when SLOs, compliance, or geographic redundancy require cross-cloud failover.
