# Secure Credential Management Plan for Kimberly Project

## Overview
This plan outlines how to securely manage credentials (API keys, database passwords, etc.) needed for the Kimberly project, ensuring that Copilot (GitHub Copilot) and developers can access them without compromising security. The approach follows best practices: no hardcoding, environment-based configuration, and layered security for dev/staging/production.

## Identified Credentials Needed
Based on project requirements:
- **LLM API Keys**: For Llama 3.1 or other models (e.g., Hugging Face token for transformers).
- **Database Credentials**: Username/password for PostgreSQL or SQLite (if remote).
- **Telemetry/Tracking Keys**: For monitoring services (e.g., Prometheus, Grafana API keys).
- **Encryption Keys**: For KMS or local encryption (future).
- **Other**: Cloud provider keys (Oracle Always Free, AWS), agent sandbox secrets.

Enforce "free-mode": Block paid API usage in CI with grep checks.

## Implementation Steps

### 1. Environment Variables as Primary Mechanism
- All credentials accessed via `os.getenv()` in Python code.
- Example in `app.py`:
  ```python
  import os
  HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
  if not HUGGINGFACE_TOKEN:
      raise ValueError("HUGGINGFACE_TOKEN not set")
  ```
- For optional creds, provide defaults or skip features.

### 2. Local Development Setup
- Use `.env` file for local env vars.
- Install `python-dotenv` in `requirements.txt`.
- Load in code: `from dotenv import load_dotenv; load_dotenv()`.
- Add `.env` to `.gitignore` (update existing file).
- Example `.env` (template in repo as `.env.example`):
  ```
  HUGGINGFACE_TOKEN=your_token_here
  DATABASE_URL=sqlite:///kimberly.db
  ```

### 3. CI/CD Security
- Use GitHub Secrets for CI pipelines.
- In `.github/workflows/ci.yml`, reference as `${{ secrets.HUGGINGFACE_TOKEN }}`.
- CI jobs: Lint for hardcoded secrets (e.g., use `detect-secrets` tool).
- Add CI step to grep for paid API calls and fail if found.

### 4. Production Secrets Management
- Use cloud secrets manager (e.g., AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault).
- For free tier: Oracle Vault or local KMS.
- Code retrieves secrets at runtime via SDKs (e.g., `boto3` for AWS).
- Rotate keys regularly; audit access logs.

### 5. Documentation and Training
- Create `docs/ENVIRONMENT_SETUP.md` (from needs-work.md) with setup instructions.
- Include in `CONTRIBUTING.md`: "Never commit credentials; use env vars."
- Add security checklist in `docs/CODE_REVIEW.md`.

### 6. Monitoring and Auditing
- Log credential access (without exposing values) for audit trails.
- Use tools like `detect-secrets` in pre-commit hooks.
- Regular security reviews as per SECURITY.md.

### 7. Free-Mode Enforcement
- CI grep for patterns like `openai.api_key`, `anthropic.`, etc.
- Environment flag `FREE_MODE=true` to disable paid features.

## Risks and Mitigations
- **Accidental Commit**: .gitignore + pre-commit hooks.
- **Runtime Exposure**: No logging of secrets; use redaction.
- **Copilot Access**: Copilot suggests code based on context; ensure .env not in workspace for suggestions.
- **PII in Tracking**: Redact `misc/copilot_tracking.json` if sensitive.

## Next Actions
- Update `.gitignore` with `.env`.
- Add `python-dotenv` to `requirements.txt`.
- Create `.env.example`.
- Implement env var loading in `app.py`.
- Add CI secrets and linting.