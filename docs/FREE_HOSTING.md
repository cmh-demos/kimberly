# Free hosting options (bootstrap)

This project recommends two practical, low-cost bootstrap options for running Kubernetes
workloads and publishing container images while we mature our IaC and CI/CD:

- Oracle Cloud — Always Free: self-managed VMs where you can run lightweight Kubernetes
  (k3s/k0s) or k3d/kind during development. Good for full control and predictable free
  quotas; requires more ops work.
- Fly.io: managed edge/app hosting (simpler than full K8s for early stages). Good for
  quick deployments, fewer infra maintenance needs.

Container registry recommendation

- Use a provider-agnostic registry such as GitHub Container Registry (`ghcr.io`) for
  images. Keeps deployments portable and avoids binding to cloud-provided registries.

CI-agnostic guidance

- Keep build and deployment pipelines provider-agnostic. Avoid hard dependency on GitHub
  Actions unless explicitly chosen later.

Local development

- Use `k3d` or `kind` for local Kubernetes testing and `docker` / `podman` for image
  builds before publishing to `ghcr.io`.

This file is intentionally short — see `ARCHITECTURE.md` and
`docs/decisions/ADR-0004.md` for migration guardrails and pros/cons.
