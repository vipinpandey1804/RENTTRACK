# Phase 0 Issues — Bulk Import Guide

Copy-paste each block below into GitHub Issues. Tag with `phase-0` and the matching scope label.

> Tip: use the [gh CLI](https://cli.github.com/) to create issues in bulk:
> ```bash
> gh issue create --title "..." --body-file issue.md --label "phase-0,backend"
> ```

---

## #1 — Set up GitHub branch protection
**Labels:** `phase-0`, `infra`, `size/S`

Protect `main` and `develop` branches:
- Require PR before merge
- Require 1 approving review
- Require status checks: `backend`, `frontend`, `security`
- Require signed commits (optional)
- No force pushes

---

## #2 — Install and wire pre-commit hooks
**Labels:** `phase-0`, `infra`, `size/S`

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Verify ruff, prettier, and secret-detection are all running on commit.

---

## #3 — Implement signup API
**Labels:** `phase-0`, `backend`, `auth`, `size/M`

- `POST /api/v1/auth/signup/` accepts email, password, full_name, role
- Creates User (unverified) + sends verification email via Mailhog
- Landlord signup creates a new Organization and Membership(owner)
- Tenant signup requires an invite token

---

## #4 — Email verification flow
**Labels:** `phase-0`, `backend`, `auth`, `size/M`

- Generate single-use token on signup
- `POST /api/v1/auth/verify-email/` accepts token, marks user verified
- Frontend route `/verify-email/:token` calls the API and redirects

---

## #5 — Tenant invite flow
**Labels:** `phase-0`, `backend`, `feature`, `size/L`

- Landlord invites tenant by email → `Invite` record created with token
- Invite email sent with signup link carrying token
- Tenant signs up, invite auto-creates Membership(tenant) + links to pre-assigned Unit
- Expires after 7 days

---

## #6 — RBAC permission classes
**Labels:** `phase-0`, `backend`, `auth`, `size/M`

- `IsOrgOwner`, `IsPropertyManager`, `IsTenantOfLease`, `IsSameOrg`
- Integration test: tenant cannot access another tenant's bills
- Integration test: landlord cannot access another org's properties

---

## #7 — Admin panel customization
**Labels:** `phase-0`, `backend`, `size/S`

- Register all models in Django admin
- Custom admin for Organization (readonly fields for tier, features)
- Filter by organization for tenant-scoped models
- Add audit log for admin actions

---

## #8 — Property CRUD API
**Labels:** `phase-0`, `backend`, `feature`, `size/M`

- `GET/POST/PATCH/DELETE /api/v1/properties/`
- DRF ViewSet with tenant-scoped queryset
- Serializers with validation
- Pagination + filtering (city, status, type)
- Tests for tenant isolation

---

## #9 — Unit CRUD API
**Labels:** `phase-0`, `backend`, `feature`, `size/M`

- `GET/POST/PATCH /api/v1/properties/{id}/units/`
- Nested under property
- Status transitions validated

---

## #10 — Lease creation API
**Labels:** `phase-0`, `backend`, `feature`, `size/L`

- `POST /api/v1/leases/` creates a lease + sends invite if tenant doesn't exist
- State machine: draft → active → ended/terminated
- Validation: no overlapping active leases per unit

---

## #11 — Frontend dashboard shell
**Labels:** `phase-0`, `frontend`, `size/M`

- Layout with sidebar navigation
- Top bar with org switcher (if user has multiple memberships)
- Responsive (mobile drawer)
- Loading + error boundaries

---

## #12 — Frontend: Properties list page
**Labels:** `phase-0`, `frontend`, `feature`, `size/M`

- Table + card view toggle
- Search + filter by city/status
- "Add property" modal
- Empty state

---

## #13 — Frontend: Property detail + units
**Labels:** `phase-0`, `frontend`, `feature`, `size/L`

- Property header with edit button
- Tabs: Units, Leases, Documents, Settings
- Inline unit add/edit
- Tenant invite modal from unit row

---

## #14 — Tenant dashboard
**Labels:** `phase-0`, `frontend`, `feature`, `size/M`

- Separate layout for tenant role
- Current unit info + lease details
- Placeholder tiles for bills, meter readings, tickets
- Account settings

---

## #15 — E2E test: landlord signup → invite → tenant login
**Labels:** `phase-0`, `qa`, `size/M`

Full Playwright test covering the golden path.

---

## #16 — Load tests baseline (k6)
**Labels:** `phase-0`, `infra`, `size/M`

Baseline load test:
- 100 concurrent users hitting `/api/v1/properties/`
- Assert p95 < 200ms, error rate < 1%
- Results stored in `docs/load-tests/baseline.md`

---

## #17 — Tenant isolation integration test suite
**Labels:** `phase-0`, `backend`, `security`, `size/M`

Required test for every tenant-scoped model:
- Create data in org A and org B
- Switch context to A, assert B invisible
- Switch context to B, assert A invisible

---

## #18 — Deploy to staging (Railway)
**Labels:** `phase-0`, `infra`, `size/L`

- Set up Railway project with backend + Postgres + Redis
- Frontend deployed to Vercel
- Automatic deploy on push to `develop`
- Staging URL shared in team channel
