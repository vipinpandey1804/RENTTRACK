# Frontend E2E Test Runner

Run Playwright end-to-end tests for the RentTrack frontend. Use this skill after completing any frontend module or before creating a PR.

## What this does

1. Checks that the frontend dev server is reachable (or notes it must be running)
2. Runs all Playwright e2e specs in `frontend/e2e/`
3. Reports pass/fail per spec file with failure details
4. Flags any regressions that must be fixed before a PR is created

## Instructions

When invoked, execute the following steps in order:

### Step 1 — Type-check the frontend first

```
!cd /home/user/RENTTRACK/frontend && npm run typecheck 2>&1
```

If type errors are found, report them and stop — fix types before running e2e.

### Step 2 — Run Playwright tests in headed-less mode

```
!cd /home/user/RENTTRACK/frontend && PLAYWRIGHT_BASE_URL=http://localhost:5173 npx playwright test --reporter=list 2>&1
```

If the dev server is not running (connection refused), inform the user:

> The frontend dev server is not running. Start it with `cd frontend && npm run dev` in another terminal, then re-run `/test-frontend`.

### Step 3 — Summarise results

After running, produce a summary table:

| Spec file | Tests | Passed | Failed | Skipped |
| --------- | ----- | ------ | ------ | ------- |

For every **failed** test, show:

- Test name
- Error message (first 5 lines)
- File + line number from the stack trace

### Step 4 — Verdict

- If **all tests pass**: state "✓ Frontend e2e tests passed — safe to create PR."
- If **any test fails**: state "✗ Frontend e2e tests FAILED — fix failures before creating PR." and list what needs fixing.

## Scope of tests

| Spec                       | Covers                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| `auth.spec.ts`             | Login, signup, email verification banner, protected route redirects                           |
| `billing.spec.ts`          | Bill table rendering, status tabs, search, date range filter, pagination, generate-bill modal |
| `tenant-dashboard.spec.ts` | Role-based routing, lease card, outstanding bills, empty states                               |

## Adding new tests

When implementing a new frontend module, add a corresponding spec in `frontend/e2e/<module>.spec.ts` following the pattern in existing specs:

- Use `seedAuth()` or `seedTenantAuth()` from `helpers.ts` to avoid real login
- Use `mockApi()` from `helpers.ts` to intercept backend calls
- Test rendering, interactions, URL sync, and empty states
