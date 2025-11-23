# Security Policy

## Supported Versions
We actively monitor and patch security vulnerabilities in the following versions:
- Latest release
- Main branch

## Reporting a Vulnerability
If you discover a security vulnerability, please report it responsibly:
- **Do not** create public GitHub issues for vulnerabilities.
- Email: security@kimberly.ai (placeholder; replace with actual contact).
- Response time: Within 48 hours.
- Include details: Description, impact, reproduction steps, and any proposed fixes.

We follow the [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) for incident response.

## Security Measures
- **Dependency Scanning**: Automated via Dependabot and Safety.
- **Code Scanning**: Bandit for Python security linting, CodeQL for general vulnerabilities.
- **Secret Scanning**: Enabled on GitHub to detect exposed secrets.
- **Branch Protection**: Requires PR reviews and CI checks for main branch.
- **Encryption**: End-to-end encryption for user data (as per design).
- **Access Control**: JWT authentication, RBAC for agents.

## Known Security Considerations
- Agent sandboxing is in development; avoid running untrusted agents in production.
- Local storage option available to minimize cloud exposure.
- Regular audits recommended for production deployments.

For more details, see `docs/threat-model.md` and `docs/RISK_ANALYSIS.md`.
