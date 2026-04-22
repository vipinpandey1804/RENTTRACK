# Backend Django Test Runner

Run pytest tests for the RentTrack Django backend. Use this skill after completing any backend module or before creating a PR.

## What this does

1. Verifies the test environment is configured (SQLite in-memory, no real Redis)
2. Runs pytest across all `apps/*/tests/` directories
3. Reports pass/fail per module with failure details
4. Flags any failures that must be fixed before a PR is created

## Instructions

When invoked, execute the following steps in order:

### Step 1 — Check for syntax/import errors first
```
!cd /home/user/RENTTRACK/backend && python -m ruff check apps/ 2>&1 | head -30
```
If ruff reports errors, fix them before running tests.

### Step 2 — Run the full pytest suite
```
!cd /home/user/RENTTRACK/backend && python -m pytest apps/ -v --tb=short -q 2>&1
```

The test settings (`config.settings.test`) use:
- SQLite in-memory (no real Postgres needed)
- `LocMemCache` (no real Redis needed)
- `CELERY_TASK_ALWAYS_EAGER = True`
- Fast MD5 password hashing

If pytest is not importable, install it:
```
!cd /home/user/RENTTRACK/backend && pip install pytest pytest-django factory-boy 2>&1 | tail -5
```
Then re-run step 2.

### Step 3 — Run a specific module (optional)

If args were passed to the skill (e.g., `/test-backend accounts`), run only that module:
```
!cd /home/user/RENTTRACK/backend && python -m pytest apps/<module>/tests/ -v --tb=short 2>&1
```

### Step 4 — Summarise results

Produce a summary table:

| Module | Tests | Passed | Failed | Errors |
|--------|-------|--------|--------|--------|

For every **failed** test, show:
- Test class + method name
- Assertion error or exception (first 8 lines of `--tb=short` output)

### Step 5 — Verdict

- If **all tests pass**: state "✓ Backend tests passed — safe to create PR."
- If **any test fails**: state "✗ Backend tests FAILED — fix failures before creating PR." and list what needs fixing.

## Test coverage by module

| Module | Test file | Covers |
|--------|-----------|--------|
| `accounts` | `test_email_verification.py` | Token generation, consumption, resend, expiry |
| `accounts` | `test_invite_flow.py` | Invite creation, validation, accept, rejection cases |
| `properties` | `test_lease_validation.py` | Overlapping lease prevention, ended lease ok, error messages |
| `billing` | `test_bill_filters.py` | Status filter, date range (gte/lte), search, org isolation |

## Adding new tests

When implementing a new backend module, add tests in `apps/<module>/tests/test_<feature>.py`:
- Mark tests with `@pytest.mark.django_db`
- Use fixtures from the local `conftest.py` for org/user/client setup
- Test: happy path, permission enforcement (401/403), validation errors (400), and org isolation
