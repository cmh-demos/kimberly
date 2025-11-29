# Disaster Recovery Plan

## Overview

This document outlines the disaster recovery (DR) strategy for Kimberly,
including backup procedures, restore testing, and recovery objectives.

## Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| RPO (Recovery Point Objective) | 24 hours | Maximum acceptable data loss |
| RTO (Recovery Time Objective) | 4 hours | Maximum acceptable downtime |

## Backup Strategy

### Database Backups (PostgreSQL)

**Frequency:** Daily backups via scheduled workflow

**Retention Policy:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Storage:**
- Backups are encrypted at rest using AES-256
- Stored in S3-compatible object storage (MinIO for self-hosted, AWS S3 for
  cloud)
- Cross-region replication recommended for production deployments

### Backup Components

1. **PostgreSQL Database**
   - Full logical backup using `pg_dump`
   - Point-in-time recovery (PITR) via WAL archiving for production

2. **Object Storage (MinIO/S3)**
   - Versioned buckets for attachments and transcripts
   - Cross-region replication for critical data

3. **Redis Cache**
   - Ephemeral data; no backup required
   - Rebuild from source on recovery

4. **Configuration Files**
   - Version controlled in Git
   - Environment-specific secrets in secrets manager

## Backup Procedures

### Automated Daily Backup

The `backup.yml` GitHub Actions workflow runs daily and performs:

1. Connect to database with read-only credentials
2. Execute `pg_dump` with compression
3. Encrypt backup file
4. Upload to configured backup storage
5. Verify upload integrity (checksum)
6. Clean up old backups per retention policy
7. Send notification on success/failure

### Manual Backup

For ad-hoc backups, use the backup script:

```bash
python scripts/backup_db.py --output /path/to/backup
```

## Restore Procedures

### Restore Verification (Automated)

Monthly automated restore tests verify backup integrity:

```bash
python scripts/verify_restore.py --backup-file /path/to/backup.sql.gz
```

The verification script:

1. Creates an isolated test database
2. Restores the backup
3. Validates data integrity (row counts, checksums)
4. Drops the test database
5. Reports success/failure

### Manual Restore

For production restore:

1. **Notify stakeholders** of planned downtime
2. **Stop application services** to prevent writes
3. **Create current backup** before restore (if possible)
4. **Restore database:**

```bash
gunzip -c backup.sql.gz | psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

5. **Verify data integrity**
6. **Restart application services**
7. **Validate application functionality**
8. **Notify stakeholders** of recovery completion

## Testing Schedule

| Test Type | Frequency | Owner |
|-----------|-----------|-------|
| Backup integrity check | Daily (automated) | CI/CD |
| Restore to test env | Monthly | @ops |
| Full DR drill | Quarterly | @engineering |

## Incident Response

### Backup Failure

1. Alert triggered via workflow notification
2. On-call engineer investigates within 1 hour
3. Manual backup initiated if automated backup fails
4. Root cause analysis documented

### Data Loss Incident

1. Identify scope and timeline of data loss
2. Determine most recent valid backup
3. Notify affected users if applicable
4. Execute restore procedure
5. Document incident and update procedures

## Roles and Responsibilities

| Role | Responsibility |
|------|----------------|
| @ops | Backup monitoring, restore execution |
| @engineering | DR process design, testing oversight |
| @security | Encryption key management, access control |

## Monitoring and Alerts

- **Backup job status**: Workflow success/failure notifications
- **Storage usage**: Alert at 80% and 90% capacity
- **Backup age**: Alert if last backup older than 25 hours

## References

- [INFRASTRUCTURE.md](./INFRASTRUCTURE.md) - Infrastructure overview
- [SECURITY_AND_RISKS.md](../SECURITY_AND_RISKS.md) - Risk register (R-010)
- [ADR-0002](./decisions/ADR-0002.md) - Data storage choice

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-26 | 1.0 | Initial version | @copilot |
