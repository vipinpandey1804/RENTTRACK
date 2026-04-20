# Architecture

High-level documentation of RentTrack's system design.

## Contents

- [System Overview](./system-overview.md) — services, data flow, infrastructure
- [Data Model](./data-model.md) — entity relationships and partitioning strategy
- [Multi-Tenancy](./multi-tenancy.md) — isolation guarantees and enforcement
- [Scale Playbook](./scale-playbook.md) — when to extract services, shard, etc.

## Quick reference

### Stack
- **Backend:** Django 5 + DRF + Celery + PostgreSQL 16 + Redis
- **Frontend:** React 18 + Vite + TypeScript + TailwindCSS
- **Infra:** Docker (dev) → Kubernetes (prod) on AWS EKS
- **Observability:** OpenTelemetry + Prometheus + Grafana + Sentry

### Service boundaries (current monolith)

```
apps/
├── core/           # Shared base models, middleware, health checks
├── accounts/       # Users, Organizations, Memberships, Auth
├── properties/     # Properties, Units, Leases
├── billing/        # Bills, BillLineItems
├── metering/       # MeterReadings (electricity, water, gas)
├── notifications/  # Email + SMS + WhatsApp dispatch
└── payments/       # Payment recording, gateway reconciliation
```

Each app is bounded — imports across apps go through public interfaces (models/serializers) only. When an app grows past ~5K lines or needs independent scaling, it's a candidate for extraction into a microservice.

## Key decisions

See [ADRs](../adr/) for the full history. Highlights:

| Decision | Status | Rationale |
|---|---|---|
| Modular monolith first, microservices later | ✅ | Small team, fast iteration, avoid premature complexity |
| PostgreSQL as the single source of truth | ✅ | ACID for money, strong ecosystem, great for multi-tenancy |
| UUID primary keys | ✅ | Safer for public APIs, easier sharding later |
| JWT for auth with refresh rotation | ✅ | Stateless, works well with mobile + web + API |
| Row-level security for tenant isolation | ✅ | Defense in depth — app bugs can't leak across tenants |
| Partition bills/payments/readings by month | ✅ | Required at 1M+ rows/table to keep queries fast |
