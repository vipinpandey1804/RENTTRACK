# How to Push This to GitHub

Since I can't push to GitHub directly from here, follow these steps — should take you 2 minutes.

## Option 1: Create a new empty repo on GitHub first

1. Go to https://github.com/new
2. Name: `renttrack`
3. Description: `Enterprise-scale tenant & property management SaaS`
4. Visibility: Private (recommended until ready) or Public
5. **DO NOT** initialize with README, .gitignore, or license (we already have them)
6. Click **Create repository**

## Option 2: Using the GitHub CLI (faster)

```bash
# Install gh CLI if needed: https://cli.github.com/
gh auth login
gh repo create vipinpandey1804/renttrack --private --description "Enterprise-scale tenant & property management SaaS"
```

## Then, from this folder

```bash
cd renttrack

# Initialize git
git init
git branch -M main

# Add all files
git add .
git commit -m "chore: initial scaffold

- Monorepo: Django backend + React frontend + Docker
- Modular apps: core, accounts, properties, billing, metering, notifications, payments
- Multi-tenancy foundation with TenantAwareModel and middleware
- JWT auth with refresh token rotation
- Frontend: Vite + React + TypeScript + Tailwind + React Query + Zustand
- CI/CD: GitHub Actions with backend + frontend + security scan
- Docs: PRD v2, architecture overview, multi-tenancy guide, Phase 0 checklist
"

# Connect to GitHub and push
git remote add origin git@github.com:vipinpandey1804/renttrack.git
git push -u origin main

# Create develop branch for ongoing work
git checkout -b develop
git push -u origin develop
```

## Post-push checklist

1. ✅ Visit `https://github.com/vipinpandey1804/renttrack` — confirm files are there
2. ✅ Settings → Branches → add branch protection for `main` (require PR + 1 review)
3. ✅ Settings → Actions → ensure CI workflow ran (first run may fail until Docker images are available — that's fine)
4. ✅ Issues → create milestone "Phase 0: Foundation"
5. ✅ Create issues from `docs/phase-0-issues.md` (paste each block, tag with `phase-0`)
6. ✅ Set default branch to `develop` (so PRs target `develop`, not `main`)

## First local test

```bash
cp .env.example .env
./scripts/setup.sh
```

Or with Make:

```bash
make build
make up
make migrate
make createsuperuser
make logs
```

Visit:
- http://localhost:5173 — frontend
- http://localhost:8000/api/docs/ — Swagger UI
- http://localhost:8000/admin/ — Django admin
- http://localhost:8025 — Mailhog (captures all outbound email in dev)
