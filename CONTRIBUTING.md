# Contributing to RentTrack

Thanks for your interest in contributing! 🎉

## Ground rules

1. **One PR, one concern.** Keep changes focused — it makes review faster.
2. **Write tests.** Backend PRs should include unit tests. Frontend PRs should include at least a smoke test for new components.
3. **Follow Conventional Commits.** Examples:
   - `feat(billing): add late fee calculation`
   - `fix(auth): handle expired refresh tokens`
   - `chore(ci): update Python version`
   - `docs(readme): update setup steps`
4. **Never commit secrets.** Use `.env` for local dev, GitHub Secrets for CI.
5. **Respect multi-tenancy.** Every new model must extend `TenantAwareModel`. Every new queryset must be scoped to the current organization.

## Development workflow

```bash
# 1. Fork the repo and clone
git clone git@github.com:YOUR_USERNAME/renttrack.git
cd renttrack

# 2. Create a feature branch from develop
git checkout develop
git checkout -b feat/amazing-feature

# 3. Make your changes and commit
git add .
git commit -m "feat(scope): describe your change"

# 4. Push and open a PR
git push origin feat/amazing-feature
```

## Branch strategy

- `main` — production. Protected. Only accepts PRs from `develop` or hotfixes.
- `develop` — integration branch. All features land here first.
- `feat/*`, `fix/*`, `chore/*` — topic branches.

## Code style

### Python / Django
- `ruff` for linting and formatting (pre-commit will run automatically).
- `mypy` for type checking — please add type hints to new code.
- Use `TenantAwareModel` as the base for any business model.
- Querysets on business data must be filtered by `organization_id` — never assume global scope.

### TypeScript / React
- Functional components with hooks only.
- Tailwind for styling — no separate CSS files unless necessary.
- Colocate related files: a page's component, hooks, and types live together.
- Use React Query for server state; Zustand for client state.

## Testing

```bash
# Backend
cd backend && pytest
cd backend && pytest apps/billing/  # single app

# Frontend
cd frontend && npm test
cd frontend && npm run test:e2e     # end-to-end

# Full stack (from repo root)
docker-compose up --build
```

### Test requirements

- **Backend**: minimum 80% line coverage for new code. Use factory-boy for fixtures.
- **Frontend**: component snapshot tests + a happy-path integration test per page.

## Pull request checklist

Before requesting a review:

- [ ] All tests pass locally
- [ ] `ruff check` and `npm run lint` are clean
- [ ] No new security warnings from Trivy
- [ ] Migrations are backward-compatible
- [ ] If the PR touches tenant-scoped models, a test asserts isolation
- [ ] `README.md` and `docs/` updated if behavior changed

## Getting help

- Ask in GitHub Discussions
- Or ping @vipinpandey1804 on the issue or PR
