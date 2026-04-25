# RentTrack

> Enterprise-scale tenant & property management SaaS — built for India's rental market.

[![CI](https://github.com/vipinpandey1804/renttrack/actions/workflows/ci.yml/badge.svg)](https://github.com/vipinpandey1804/renttrack/actions)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.0-green)
![React](https://img.shields.io/badge/react-18-blue)
![License](https://img.shields.io/badge/license-MIT-green)

RentTrack digitizes the landlord-tenant relationship: rent collection, electricity/utility tracking, maintenance requests, and automated email + SMS notifications. Designed multi-tenant from day one to scale from solo landlords to professional property management companies.

## 🏗️ Architecture

This is a **monorepo** with a modular Django backend and a React/Vite frontend.

```
renttrack/
├── backend/              # Django + DRF API
│   ├── apps/
│   │   ├── core/         # Shared utilities, base models, tenancy middleware
│   │   ├── accounts/     # Auth, users, RBAC, organizations
│   │   ├── properties/   # Properties, units, leases
│   │   ├── billing/      # Bill generation, invoices, late fees
│   │   ├── metering/     # Meter readings, tariffs, consumption
│   │   ├── notifications/# Email, SMS, WhatsApp delivery
│   │   └── payments/     # Gateway integrations, reconciliation
│   ├── config/           # Django settings (dev, prod, test)
│   └── scripts/          # Management scripts, seeders
├── frontend/             # React + Vite + TailwindCSS
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Route-level pages
│       ├── hooks/        # Custom React hooks
│       ├── lib/          # API client, utilities
│       └── store/        # State management (Zustand)
├── docker/               # Dockerfiles and docker-compose configs
├── docs/                 # Architecture docs, API specs, runbooks
└── .github/              # CI/CD workflows, issue templates
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- Git

### Run Everything with Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/vipinpandey1804/renttrack.git
cd renttrack

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up --build
```

Services that come up:

- **Backend API** → http://localhost:8000
- **Frontend** → http://localhost:5173
- **PostgreSQL** → localhost:5432
- **Redis** → localhost:6379
- **Mailhog (email testing)** → http://localhost:8025

### Local Development (without Docker)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Background worker (Celery):**

```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info  # For scheduled tasks
```

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# E2E tests
npm run test:e2e
```

## 📋 Environment Variables

See `.env.example` for all available configuration. Critical ones:

| Variable           | Purpose                      | Required  |
| ------------------ | ---------------------------- | --------- |
| `DATABASE_URL`     | PostgreSQL connection string | ✅        |
| `REDIS_URL`        | Redis connection string      | ✅        |
| `SECRET_KEY`       | Django secret key            | ✅        |
| `JWT_SECRET`       | JWT signing key              | ✅        |
| `SENDGRID_API_KEY` | Email provider               | Prod only |
| `MSG91_AUTH_KEY`   | SMS provider (India)         | Prod only |
| `RAZORPAY_KEY_ID`  | Payment gateway              | Prod only |

## 📊 Project Status

| Phase                    | Status         | Target    |
| ------------------------ | -------------- | --------- |
| Phase 0: Foundation      | 🟡 In Progress | Week 1–2  |
| Phase 1: MVP             | ⚪ Planned     | Week 3–4  |
| Phase 2: Metering + SMS  | ⚪ Planned     | Week 5–6  |
| Phase 3: Payments        | ⚪ Planned     | Week 7–8  |
| Phase 4: Scale Hardening | ⚪ Planned     | Week 9–12 |

See [PRD](./docs/PRD.md) for the full rollout plan.

## 🤝 Contributing

1. Fork the repo and create your feature branch (`git checkout -b feature/amazing-feature`)
2. Commit your changes (`git commit -m 'feat: add amazing feature'`) — follow [Conventional Commits](https://www.conventionalcommits.org/)
3. Push to the branch (`git push origin feature/amazing-feature`)
4. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for code style, testing requirements, and the review process.

## 📚 Documentation

- [Product Requirements Document](./docs/PRD.md) — full vision and scale targets
- [Architecture Overview](./docs/architecture/README.md) — system design decisions
- [API Documentation](./docs/api/README.md) — REST API reference
- [Database Schema](./docs/architecture/data-model.md) — entity relationships

## 📄 License

MIT © 2026 Vipin Pandey
