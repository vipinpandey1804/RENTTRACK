# Phase 0: Foundation Setup

This is where we are right now. Target: get a clean, working local development loop with auth and empty apps in place.

## Checklist

### Day 1-2: Repo & Infrastructure
- [x] Monorepo structure (backend + frontend + docker)
- [x] Docker Compose (Postgres + Redis + Mailhog + backend + frontend + Celery)
- [x] CI workflow (lint + test + build)
- [x] Issue/PR templates
- [ ] GitHub branch protection on `main` and `develop`
- [ ] Pre-commit hooks installed

### Day 3-4: Django Foundation
- [x] Project structure with modular apps
- [x] Settings split: base / dev / prod / test
- [x] Base models (TenantAwareModel, UUIDModel, TimeStampedModel, SoftDeleteModel)
- [x] Tenant context middleware
- [x] Health check endpoints
- [ ] Initial migrations committed
- [ ] `createsuperuser` flow tested
- [ ] Admin panel accessible

### Day 5-6: Auth
- [x] User + Organization + Membership models
- [x] JWT login + refresh endpoints (stub)
- [ ] Signup flow (with email verification via Mailhog)
- [ ] Phone verification via SMS OTP (MSG91 sandbox)
- [ ] Tenant invite flow (landlord invites tenant → tenant completes signup)
- [ ] RBAC permission classes
- [ ] Auth tests

### Day 7-8: Frontend Bootstrap
- [x] Vite + React + TypeScript + Tailwind
- [x] React Router + React Query + Zustand
- [x] Login page + protected routes
- [ ] Dashboard shell with navigation
- [ ] Settings page
- [ ] Form components (input, button, select, toast)
- [ ] E2E test for login flow

### Day 9-10: First Feature — Properties
- [x] Property + Unit + Lease models
- [ ] Property CRUD API
- [ ] Property list + detail pages
- [ ] Unit management inside property detail
- [ ] Tenant invite modal
- [ ] Integration tests for tenant scoping

## How to track

Create a GitHub Milestone called "Phase 0" and convert each unchecked item above into an issue. Labels: `phase-0`, `backend` / `frontend` / `infra`, and a size label (`size/S`, `size/M`, `size/L`).

## Exit criteria

Phase 0 is done when:
1. `docker-compose up` starts everything cleanly on a fresh checkout.
2. A landlord can sign up, log in, create a property + unit, and invite a tenant via email.
3. The tenant can accept the invite, complete signup, and see their unit in their dashboard.
4. CI is green on every PR.
5. All tenant isolation tests pass.

After Phase 0 we begin Phase 1: billing engine + rent bill generation.
