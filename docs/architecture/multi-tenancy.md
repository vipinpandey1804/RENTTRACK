# Multi-Tenancy

Multi-tenant data isolation is non-negotiable. A cross-tenant data leak is an existential event for a SaaS — this document defines how RentTrack prevents it.

## Levels of isolation

RentTrack uses **three defense layers**:

1. **Application layer** — every queryset is scoped to `organization_id` via the `TenantAwareManager`.
2. **Middleware layer** — `TenantContextMiddleware` extracts the current org from the JWT and stores it in thread-local state.
3. **Database layer** — PostgreSQL Row-Level Security (RLS) policies enforce isolation even if the application has a bug.

Any single layer failing is survivable. All three failing simultaneously is what we design against.

## The tenant boundary

Every business entity in RentTrack descends from an `Organization`. The `Organization` is the tenant boundary — nothing crosses it except explicitly via privileged super-admin flows with full audit logging.

```
Organization (tenant root)
├── Memberships (users + roles)
├── Properties
│   └── Units
│       └── Leases
│           ├── Bills
│           │   └── Payments
│           ├── MeterReadings
│           └── MaintenanceTickets
└── Notifications
```

## Enforcement patterns

### 1. Base model

Every tenant-scoped model extends `TenantAwareModel`:

```python
class Bill(TenantAwareModel):
    lease = models.ForeignKey(...)
    total_amount = models.DecimalField(...)
```

This guarantees an `organization` FK exists and is indexed.

### 2. Tenant-scoped manager

Default queryset auto-filters by current org:

```python
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        org_id = get_current_organization_id()
        qs = super().get_queryset()
        if org_id:
            qs = qs.filter(organization_id=org_id)
        return qs
```

### 3. Middleware

`TenantContextMiddleware` runs before every view:

- Reads JWT claim `org`
- Sets thread-local `organization_id`
- Sets Postgres session variable `app.current_org` (used by RLS)

### 4. PostgreSQL RLS

For production, enable RLS on every tenant-scoped table:

```sql
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON bills
  USING (organization_id::text = current_setting('app.current_org', true));
```

Even a raw SQL query from a buggy admin tool cannot return rows from another tenant.

## Tiers

| Tier          | DB isolation                             | Who        |
| ------------- | ---------------------------------------- | ---------- |
| **Shared**    | Same cluster, same schema, RLS-enforced  | Free/Pro   |
| **Pooled**    | Same cluster, dedicated schema per org   | Business   |
| **Dedicated** | Dedicated RDS instance + Redis namespace | Enterprise |

## Testing

Every PR that touches a tenant-scoped model must include a test that:

1. Creates two organizations, A and B.
2. Creates data in both.
3. Sets context to A and asserts that B's data is invisible.

See `backend/apps/core/tests/test_tenancy.py` for the reference pattern.

## Breaking changes

Anything that weakens tenant isolation — even temporarily — is a breaking change. It requires:

- An ADR documenting why
- Security review
- Rollback plan
- Audit log entry
