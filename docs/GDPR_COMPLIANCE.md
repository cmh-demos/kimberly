# GDPR Compliance Documentation

This document describes the GDPR (General Data Protection Regulation) compliance
implementation for the Kimberly AI Assistant.

## Overview

Kimberly implements comprehensive GDPR compliance features to protect user data
and ensure regulatory compliance. The implementation covers:

- **Article 17**: Right to Erasure (Right to be Forgotten)
- **Article 20**: Right to Data Portability
- **Article 30**: Records of Processing Activities (Audit Logging)

## API Endpoints

### Data Export (Article 20)

The data export functionality allows users to request a complete export of their
personal data in a portable format.

#### `POST /user/export`

Initiates a data export request.

**Request:**
```json
{
  "format": "json",
  "include_metadata": true
}
```

**Response (202 Accepted):**
```json
{
  "export_id": "exp_abc123",
  "status": "pending",
  "created_at": "2025-11-26T10:00:00Z",
  "expires_at": "2025-12-03T10:00:00Z"
}
```

#### `GET /user/export/{export_id}`

Check the status of an export request.

**Response:**
```json
{
  "export_id": "exp_abc123",
  "status": "completed",
  "progress_percent": 100,
  "download_url": "https://storage.kimberly.local/exports/...",
  "created_at": "2025-11-26T10:00:00Z",
  "completed_at": "2025-11-26T10:05:00Z",
  "expires_at": "2025-12-03T10:00:00Z"
}
```

### Data Deletion (Article 17)

The data deletion functionality allows users to request permanent deletion of
all their personal data.

#### `POST /user/delete`

Initiates a data deletion request.

**Request:**
```json
{
  "confirm": true,
  "reason": "Optional reason for deletion"
}
```

**Response (202 Accepted):**
```json
{
  "deletion_id": "del_xyz789",
  "status": "pending",
  "created_at": "2025-11-26T10:00:00Z"
}
```

#### `GET /user/delete/{deletion_id}`

Check the status of a deletion request.

**Response:**
```json
{
  "deletion_id": "del_xyz789",
  "status": "completed",
  "progress_percent": 100,
  "data_types_deleted": [
    "profile",
    "memories",
    "chat_history",
    "preferences"
  ],
  "created_at": "2025-11-26T10:00:00Z",
  "completed_at": "2025-11-26T10:10:00Z"
}
```

### Audit Logging (Article 30)

All data access, modifications, exports, and deletions are logged for compliance
tracking.

#### `GET /audit/logs`

Retrieve audit logs for the authenticated user.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Results per page (default: 50, max: 100)
- `action` (string): Filter by action type
- `start_date` (datetime): Filter by start date
- `end_date` (datetime): Filter by end date

**Action Types:**
- `data_export_requested`
- `data_export_completed`
- `data_deletion_requested`
- `data_deletion_completed`
- `consent_updated`
- `data_accessed`
- `data_modified`
- `login`
- `logout`
- `settings_changed`

**Response:**
```json
{
  "items": [
    {
      "id": "log_001",
      "timestamp": "2025-11-26T10:00:00Z",
      "user_id": "user_123",
      "action": "data_export_requested",
      "resource_type": "user_data",
      "resource_id": "exp_abc123",
      "details": {
        "format": "json"
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0..."
    }
  ],
  "page": 1,
  "per_page": 50,
  "total": 1
}
```

### Retention Policies

Users can configure how long their data is retained before automatic deletion.

#### `GET /compliance/retention-policies`

Retrieve current retention policies.

**Response:**
```json
{
  "policies": [
    {
      "id": "pol_001",
      "name": "Chat History Retention",
      "data_type": "chat_history",
      "retention_days": 365,
      "auto_delete": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### `PUT /compliance/retention-policies`

Update retention policies.

**Request:**
```json
{
  "policies": [
    {
      "data_type": "chat_history",
      "retention_days": 180,
      "auto_delete": true
    }
  ]
}
```

**Data Types:**
- `chat_history`
- `memory_short_term`
- `memory_long_term`
- `memory_permanent`
- `audit_logs`
- `telemetry`

### Compliance Check

Run automated compliance checks to verify GDPR requirements are met.

#### `GET /compliance/check`

**Response:**
```json
{
  "check_id": "chk_001",
  "timestamp": "2025-11-26T10:00:00Z",
  "overall_status": "compliant",
  "checks": [
    {
      "name": "Data Encryption",
      "status": "passed",
      "message": "All data at rest is encrypted"
    },
    {
      "name": "Retention Policies",
      "status": "passed",
      "message": "Retention policies are properly configured"
    },
    {
      "name": "Audit Logging",
      "status": "passed",
      "message": "Audit logging is enabled"
    },
    {
      "name": "Data Export",
      "status": "passed",
      "message": "Data export functionality is available"
    },
    {
      "name": "Data Deletion",
      "status": "passed",
      "message": "Data deletion functionality is available"
    },
    {
      "name": "Consent Management",
      "status": "passed",
      "message": "Consent tracking is enabled"
    }
  ]
}
```

## Default Retention Policies

The following default retention policies are applied:

| Data Type | Retention Days | Auto Delete |
|-----------|----------------|-------------|
| Chat History | 365 | Yes |
| Short-term Memory | 7 | Yes |
| Long-term Memory | 365 | Yes |
| Permanent Memory | 0 (indefinite) | No |
| Audit Logs | 730 (2 years) | Yes |
| Telemetry | 90 | Yes |

## Implementation Details

The GDPR compliance implementation is located in `src/api/compliance.py` and
includes:

### Services

1. **AuditLogger**: Logs all auditable actions with timestamp, user, action
   type, and metadata.

2. **DataExportService**: Handles data export requests, tracks progress, and
   provides download URLs.

3. **DataDeletionService**: Manages data deletion requests, tracks progress,
   and confirms complete deletion.

4. **RetentionPolicyService**: Manages user-configurable retention policies
   with default values.

5. **ComplianceChecker**: Runs automated compliance checks against GDPR
   requirements.

### Data Flow

1. **Export Request Flow:**
   ```
   User -> POST /user/export -> Export Service -> Audit Log -> Queue Job
                                                            -> Return export_id
   Background Worker -> Process Data -> Generate File -> Update Status
   User -> GET /user/export/{id} -> Download URL
   ```

2. **Deletion Request Flow:**
   ```
   User -> POST /user/delete -> Deletion Service -> Audit Log -> Queue Job
                                                              -> Return deletion_id
   Background Worker -> Delete Profile -> Delete Memories -> Delete Chat
                     -> Delete Preferences -> Update Status -> Audit Log
   User -> GET /user/delete/{id} -> Confirmation
   ```

## Testing

Comprehensive tests are available in `tests/test_compliance.py`:

```bash
python -m pytest tests/test_compliance.py -v
```

Tests cover:
- Audit logging functionality
- Data export request and status tracking
- Data deletion request and completion
- Retention policy management
- Compliance check execution
- Service singleton behavior

## Security Considerations

1. **Authentication**: All endpoints require JWT Bearer authentication.

2. **Authorization**: Users can only access their own data and logs.

3. **Audit Trail**: All operations are logged with IP address and user agent.

4. **Data Encryption**: Exported data should be encrypted in transit and at
   rest.

5. **Retention**: Export download URLs expire after 7 days.

## Compliance Checklist

- [x] Data export endpoint (Article 20)
- [x] Data deletion endpoint (Article 17)
- [x] Audit logging (Article 30)
- [x] Retention policies
- [x] Automated compliance checks
- [x] API documentation
- [x] Test coverage
- [ ] Integration with storage backend (pending implementation)
- [ ] Email notifications for export/deletion completion
- [ ] Admin dashboard for compliance monitoring
