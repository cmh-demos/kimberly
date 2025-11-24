# Roles & Agents

This file consolidates the `roles.md` responsibilities reference and the
`README- agents.md` summary of VSCode Copilot agent participants into a single
reference for roles and agent behavior.

## Roles and Responsibilities — Overview

This section contains key roles required to complete the Kimberly project, a
personal AI assistant with conversational chat, memory management, and agent
delegation. Each role includes a brief description and primary responsibilities.

(Detailed roles content follows — see sections below for Backend, Frontend,
Engineering Lead, SRE, DevOps, QA, Security, Privacy, Legal, Product, Design,
and specialized roles.)

## Agents in VS Code (Copilot participants)

Kimberly includes a VS Code extension with custom Copilot chat agents to help
different aspects of the project. Agent participants include (examples):

- `@backend-developer` — Backend Developer agent (server-side, APIs, memory
  management)
- `@frontend-developer` — Frontend Developer agent (UI, client-side flows)
- `@engineering-lead` — Engineering Lead agent (architecture, decisions)
- `@sre` — Site Reliability Engineer agent
- `@devops-engineer` — DevOps / infra agent
- `@qa-engineer` — QA and test specialist agent
- `@security-engineer` — Security and threat modeling agent
- `@privacy-data-engineer` — Privacy & data compliance agent
- `@legal-advisor` — Legal compliance & LLM licensing agent
- `@product-manager` — Product flow & prioritization agent
- `@ui-ux-designer` — UI/UX and wireframe agent
- `@branding-manager` — Brand guidance agent
- `@ml-engineer` — ML / LLM and embeddings agent
- `@api-engineer` — API design & OpenAPI agent
- `@documentation-engineer` — Docs & runbooks agent

### Inter-agent communication

Agents can be mentioned in chat using `@agent-id` and will provide perspective-
based responses — the extension supports multi-agent responses, allowing you to
consult multiple roles in one message and gather cross-functional feedback.

---

For the full, detailed role descriptions, see the source material in the file history or reach out
to the engineering lead about role assignments. This consolidated doc is intended as a single place
to look up role responsibilities and agent participants.
