# API Overview

This document provides a concise overview of the Kimberly REST API and links to the OpenAPI definition in `docs/openapi.yaml`.

## Authentication
- JWT Bearer tokens (issued on login/signup).
- All protected endpoints require `Authorization: Bearer <token>`.

## Core endpoints (summary)
- POST /signup — create an account and receive JWT
- POST /login — authenticate and receive JWT
- POST /chat — send a message to the conversational AI
- GET /memory — list memory items
- POST /memory — add memory
- DELETE /memory/{id} — remove memory
- GET /agents — list available agents
- POST /agents/{id}/run — invoke an agent
- GET /health — service health

For full request/response details and schemas see `docs/openapi.yaml`.

## Publishing container images (CI-agnostic)

- Recommended registry: GitHub Container Registry (`ghcr.io`) — provider-agnostic and well-supported for private and public images.
- Use explicit, immutable tags (eg. `ghcr.io/<org>/kimberly:<semver>-<sha>`) and a stable `latest` branch tag for development flows.
- Keep CI pipelines vendor-agnostic; any CI system that can build, test, sign (optional), and push to `ghcr.io` will work. Avoid bake-in to a single provider at this stage.
