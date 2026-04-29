# RentTrack — Enterprise-Scale Tenant & Property Management SaaS

**Product Requirements Document**
**Version 2.0** · Scale-Ready Architecture · April 2026

|                    |                                                    |
| ------------------ | -------------------------------------------------- |
| **Author**         | Vipin Pandey                                       |
| **Status**         | Draft — architecture review                        |
| **Scale Target**   | 100K+ landlords, 1M+ tenants, multi-region         |
| **Platform Type**  | Multi-tenant B2B2C SaaS                            |
| **Target Release** | MVP in 10–12 weeks, production-hardened by month 6 |

---

## 1. Vision & Scale Ambition

RentTrack is building the operating system for India's residential and commercial rental market. We are not a tool for one landlord managing five tenants — we are a multi-tenant SaaS platform designed to serve everyone from a solo landlord with two flats to professional property management companies running 10,000+ units across multiple cities.

> **Scale targets (24 months)**
> 100,000 active landlords · 1,000,000 active tenants · 50,000 concurrent users at peak · 10M+ notifications/month · 99.95% uptime SLA · sub-200ms p95 API latency · multi-region deployment (India primary, Southeast Asia + Middle East secondary)

---

## 2. Core Architecture Principles

- **Multi-tenancy first.** Every table carries a `tenant_id` (organization). Row-level security enforced at DB layer, not application layer.
- **Stateless services.** No in-memory session state. Every service horizontally scalable behind a load balancer.
- **Event-driven.** Core state changes publish events to Kafka/Redpanda. Downstream services subscribe — no tight coupling.
- **CQRS where it matters.** Write path optimized for correctness (Postgres), read path for speed (Redis + ElasticSearch for reports and analytics).
- **Async-by-default.** Anything slower than 50ms goes to a queue — bill generation, notifications, PDF rendering, reports.
- **Idempotent APIs.** Every write endpoint accepts an `Idempotency-Key` header. Critical for payments and notifications.
- **Observable.** Every request traced (OpenTelemetry), every error alerted (Sentry), every SLO tracked (Grafana).
- **Fail safely.** Circuit breakers around third-party dependencies (SMS, email, payment gateways). Degraded mode never takes the platform down.

---

## 3. System Architecture

### 3.1 Service Breakdown (Modular Monolith → Microservices)

Start as a modular Django monolith with clearly bounded contexts. Extract to microservices only when a service has genuine scale or team autonomy needs — not prematurely.

| Service / Module         | Extract When | Responsibility                                                  |
| ------------------------ | ------------ | --------------------------------------------------------------- |
| **Identity Service**     | Month 3      | Auth, JWT, OAuth, RBAC, session management, MFA                 |
| **Property Service**     | Month 6+     | Properties, units, leases, tenant assignments                   |
| **Billing Service**      | Month 4      | Bill generation, invoice rules, tax calculation, late fees      |
| **Payments Service**     | Month 4      | Gateway integrations, reconciliation, refunds, payouts          |
| **Metering Service**     | Month 5      | Meter readings, OCR, consumption analytics, tariff engine       |
| **Notification Service** | Month 3      | Email, SMS, WhatsApp, push — with retry, templating, throttling |
| **Ticketing Service**    | Month 9+     | Maintenance tickets, vendor assignment, SLA tracking            |
| **Document Service**     | Month 9+     | S3-backed vault, signed URLs, virus scanning                    |
| **Analytics Service**    | Month 6      | Aggregated reports, exports, warehouse pipelines                |
| **Admin/BI Service**     | Month 9+     | Internal tools, customer support console, fraud detection       |

### 3.2 Request Flow (Steady State)

```
Client → CloudFront/Cloudflare CDN → API Gateway (Kong/AWS API GW)
       → Load Balancer → Django API pods (Kubernetes, HPA)
       → PgBouncer → PostgreSQL primary/replicas
```

Reads that don't need strict consistency hit Redis cache first, then read replicas. Writes publish events to Kafka. Celery/Temporal workers subscribe and handle async work: notifications, reports, PDF generation, third-party webhooks.

### 3.3 Data Tier

- **Primary DB:** PostgreSQL 16 with logical replication. Managed via AWS RDS / Aiven for HA.
- **Read replicas:** At least 2, auto-scaling. All analytical queries routed here.
- **Partitioning:** Tables like `bills`, `payments`, `notifications`, `meter_readings` partitioned by month (declarative partitioning). Old partitions archived to cold storage after 24 months.
- **Sharding strategy:** Month 12+: shard by `organization_id` once single cluster > 2TB or > 30K writes/sec. Use Citus or app-level sharding.
- **Cache:** Redis Cluster — used for sessions, rate limiting, hot reads (tenant profiles, property configs), and Celery broker.
- **Search:** ElasticSearch / OpenSearch for tenant/property search, notification search, and audit log queries.
- **Warehouse:** ClickHouse or BigQuery for analytics/BI. Fed by CDC (Debezium) from Postgres.
- **Object Storage:** S3 / R2 for documents, meter photos, receipts. Lifecycle rules move to Glacier after 1 year.

### 3.4 Infrastructure

- **Compute:** Kubernetes (EKS/GKE). Start with 3 node groups: `api` (burst), `workers` (steady), `system` (monitoring).
- **IaC:** Terraform for cloud resources, Helm + ArgoCD for Kubernetes deployments. GitOps end-to-end.
- **Networking:** VPC with private subnets for DB/cache; NAT gateway for egress; WAF in front of API gateway.
- **Regions:** Primary `ap-south-1` (Mumbai). Secondary `ap-southeast-1` (Singapore) for DR and SEA expansion. Active-active by month 18.
- **CDN:** Cloudflare for static assets, documents (signed URLs), and DDoS protection.

---

## 4. Multi-Tenancy Model

Three isolation tiers to serve different customer segments:

| Tier                       | Isolation                                                     | Who it's for                                        |
| -------------------------- | ------------------------------------------------------------- | --------------------------------------------------- |
| **Shared (Free/Pro)**      | Shared DB, row-level security via `organization_id`           | Solo landlords, small PMCs up to 500 units          |
| **Pooled (Business)**      | Shared cluster, dedicated schema per org                      | Mid-market PMCs, 500–5000 units                     |
| **Dedicated (Enterprise)** | Dedicated DB instance + Redis namespace, optional VPC peering | Large PMCs, 5000+ units, compliance-heavy customers |

- **Tenant context middleware:** Every request carries `organization_id` in JWT. Middleware sets Postgres session variable `app.current_org`, and RLS policies enforce isolation.
- **No cross-tenant queries.** Ever. Even internal admin tools go through an explicit "impersonate" flow with audit logging.
- **Per-tenant rate limits.** Default 1000 req/min; Enterprise can negotiate higher. Prevents a noisy tenant from degrading others.
- **Per-tenant configuration.** Feature flags, branding, notification templates, tariff rules — all tenant-scoped.

---

## 5. Feature Design for Scale

### 5.1 Authentication & Identity

- JWT access token (15 min) + refresh token (30 days) stored `httpOnly`.
- MFA via TOTP (Google Authenticator) for landlords and admin roles; SMS OTP fallback.
- OAuth: Google, Apple. SAML/SSO for Enterprise tier (Okta, Azure AD).
- Granular RBAC: Super Admin, Org Owner, Property Manager, Accountant, Support Agent, Tenant, Co-tenant.
- Session invalidation on password change, role change, or suspicious activity.
- Brute-force protection: exponential backoff + CAPTCHA after 3 failures.
- Device fingerprinting for fraud detection.

### 5.2 Billing Engine

The billing engine is the heart of the platform. It must be deterministic, auditable, and handle 1M+ bills/month.

- Rule-based engine: each lease has a billing profile (rent schedule, tariff slab, tax rules, late fee rules).
- Billing cron runs daily, generates bills for all leases due that day. Parallelized by shard/partition.
- Idempotent generation — re-running same day doesn't duplicate bills (unique constraint on `lease_id + period`).
- Every bill carries line items (rent, electricity, water, maintenance, late fee, tax) — never a single opaque amount.
- Immutable once issued. Corrections happen via credit notes, not mutation.
- Supports prorated billing, mid-month move-in/out, and custom billing cycles (monthly, quarterly, advance payment).
- Tax engine: GST (India), VAT-ready for SEA/ME expansion. Pluggable per country.

### 5.3 Notification Service (The Critical Scale Bottleneck)

> ⚠️ **Why this needs special attention**
> At 1M tenants, a single 'rent due' reminder = 1M SMS + 1M emails in a 6-hour window. Cost, deliverability, and rate-limit management are the difference between a business that works and one that bleeds cash.

- **Templating system:** Handlebars-style templates per event type × language × channel, versioned, with A/B testing support.
- **Multi-provider abstraction:** primary + fallback for each channel (e.g., MSG91 primary → Twilio fallback for SMS).
- **Rate limiting:** respect each provider's throughput; queue overflow to backup provider.
- **Batching:** bulk sends for transactional emails where per-user personalization is minimal.
- **Delivery receipts** ingested via webhooks — track bounced, delivered, opened, clicked.
- **Smart channel selection:** if SMS bounces 3× for a number, fall back to email + in-app. ML-based channel preference learning over time.
- **Suppression lists** per tenant: unsubscribes, complaints, invalid numbers.
- **Cost tracking:** every send logs cost in microcents; daily rollup per organization for billing.
- **DND compliance:** India TRAI DLT registration for SMS, CAN-SPAM/GDPR for email.
- **WhatsApp Business API** as first-class channel (huge India ROI).
- **Quiet hours:** no notifications 10 PM – 7 AM local time unless emergency.

### 5.4 Electricity & Metering at Scale

- Time-series table for `meter_readings` partitioned monthly — 100K properties × 12 readings/year = 1.2M rows/year easily.
- OCR pipeline: tenant uploads meter photo → async worker (AWS Textract or custom model) → extracts reading → landlord confirms.
- IoT-ready: future support for smart meters streaming readings via MQTT → ingestion service → time-series DB (TimescaleDB).
- Anomaly detection: statistical model flags readings that are >2σ from unit's historical consumption or rollback readings.
- Bulk reading upload for PMCs: CSV import for 100+ units at once.

### 5.5 Payments at Scale

- **Multi-gateway:** Razorpay (primary India), Stripe (international), Cashfree (fallback).
- **Intelligent routing:** route based on success rates, cost, and payment method (UPI via Razorpay, cards via Stripe, etc.).
- **Automatic reconciliation:** gateway webhook → match bill → update ledger → trigger receipt.
- **Payouts to landlords:** scheduled settlements (T+2 or T+7 configurable) with PMC-level reconciliation.
- Refund flow with full audit trail and accounting entries.
- **PCI DSS scope minimization** — never touch card numbers, always tokenize via gateway.
- **Auto-pay:** mandates via UPI AutoPay / eNACH for recurring rent collection.

### 5.6 Reports & Analytics

- Real-time dashboards via materialized views refreshed every 5 min for small orgs, hourly for large.
- Heavy reports (annual, multi-property) generated async, delivered via email link with signed URL.
- Data warehouse (ClickHouse) powers custom queries and exports.
- PMC customers get API access to their own data (read-only).

---

## 6. Performance Targets & SLOs

| Metric                       | Target              | Measured At                |
| ---------------------------- | ------------------- | -------------------------- |
| API availability             | 99.95%              | Per region, 30-day rolling |
| API latency p50              | < 80ms              | Gateway → response         |
| API latency p95              | < 200ms             | Gateway → response         |
| API latency p99              | < 500ms             | Gateway → response         |
| Bill generation throughput   | 10K bills/min       | Per worker cluster         |
| Notification send latency    | < 30 sec from event | p95                        |
| Payment webhook → reconciled | < 10 sec            | p95                        |
| Dashboard load               | < 1.5 sec           | First contentful paint     |
| Report (async) turnaround    | < 5 min             | p95 for <100K rows         |
| RPO (Recovery Point)         | ≤ 5 minutes         | Managed DB backups + WAL   |
| RTO (Recovery Time)          | ≤ 30 minutes        | Full region failover       |

---

## 7. Security & Compliance

### 7.1 Security Baseline

- **Encryption at rest:** AES-256 for DB, S3, backups. Customer-managed keys (KMS) for Enterprise tier.
- **Encryption in transit:** TLS 1.3 only. HSTS enforced. No mixed content.
- **Secrets management:** AWS Secrets Manager / HashiCorp Vault. No secrets in env vars or code.
- **Network:** zero-trust within VPC. Services talk via mTLS (service mesh: Istio or Linkerd).
- **Vulnerability scanning:** Snyk/Dependabot for deps, Trivy for container images, weekly DAST scans.
- **Bug bounty** program (HackerOne) from month 6.
- **Pen test** annually by an external firm.

### 7.2 Data Privacy & Compliance

- **DPDP Act 2023 (India)** compliant — consent management, data fiduciary obligations, breach notifications.
- **GDPR-ready** for future EU expansion — right to access, erasure, portability, rectification.
- **SOC 2 Type II** audit by month 12 — required to sell to Enterprise PMCs.
- **ISO 27001** roadmap by month 18.
- **Data residency:** Indian customer data stays in `ap-south-1`. Configurable per Enterprise customer.
- **PII handling:** Aadhaar, PAN, bank details encrypted with field-level encryption in addition to DB-level.
- **Audit log:** every admin action + every data access on sensitive fields logged, immutable, 7-year retention.

### 7.3 Fraud & Abuse

- Rate limiting per IP, per user, per organization.
- Velocity checks on payments, meter readings, and bill disputes.
- ML-based anomaly detection for suspicious patterns (e.g., rapid tenant creation/deletion).
- Manual review queue for flagged transactions.

---

## 8. Reliability & Operations

### 8.1 High Availability

- Multi-AZ deployment within primary region. All stateful services replicated across 3 AZs.
- DB failover: automated via RDS Multi-AZ; replica promoted in < 60 sec.
- Graceful degradation: if notifications service is down, bills still generate — notifications retry when it recovers.
- Circuit breakers: Hystrix/Resilience4j patterns around every third-party call.
- Bulkheads: separate thread pools/workers for critical vs. non-critical paths.

### 8.2 Disaster Recovery

- Continuous backups via WAL shipping (RPO 5 min).
- Cross-region replica in secondary region (warm standby).
- Quarterly DR drills — full failover to secondary, validated, documented.
- Runbooks for every critical incident type, stored in Notion + on-call escalation.

### 8.3 Observability

- **Logs:** structured JSON, shipped to Loki/ELK. 30-day hot, 1-year cold.
- **Metrics:** Prometheus + Grafana. Dashboards per service + global platform health.
- **Tracing:** OpenTelemetry → Jaeger/Tempo. 100% sampling on errors, 1% on success.
- **Alerting:** PagerDuty for on-call. SLO-based alerting (not threshold-based) — alert when error budget burn rate is unsustainable.
- **Customer-facing status page:** status.renttrack.com, auto-updated from monitoring.

### 8.4 Deployment

- Trunk-based development. Feature flags (LaunchDarkly/Unleash) for gated rollouts.
- **CI:** GitHub Actions — lint, type-check, unit tests, integration tests, security scan. < 10 min pipeline.
- **CD:** ArgoCD GitOps. Canary deploys (5% → 25% → 100%) with automated rollback on error rate spike.
- Blue-green for DB migrations; zero-downtime schema changes using expand-contract pattern.
- Staging mirrors production (scaled-down) with anonymized prod data.

---

## 9. Data Model Highlights (Scale-Aware)

- `organizations` — root tenant entity; every table descends from here.
- `users` — partitioned by `organization_id` hash once > 10M rows.
- `properties`, `units`, `leases` — hierarchical, heavily indexed on `organization_id + status`.
- `bills` — partitioned by month, indexed on `(organization_id, due_date, status)`.
- `payments` — partitioned by month, idempotency key unique per organization.
- `meter_readings` — partitioned by month; time-series optimized with BRIN indexes.
- `notifications` — partitioned by month; 90-day retention in hot storage, archived after.
- `audit_logs` — append-only, immutable, partitioned by month, 7-year retention.
- `outbox` — transactional outbox pattern for reliable event publishing to Kafka.

---

## 10. APIs & Integrations

- Public REST API v1 with OpenAPI 3 spec, versioned via URL path (`/api/v1/...`).
- GraphQL endpoint for complex dashboard queries (read-only).
- **Webhook platform:** customers can subscribe to events (`bill.created`, `payment.received`, `ticket.updated`).
- API keys per organization with scoped permissions and per-key rate limits.
- Developer portal with interactive docs, API playground, and SDK downloads.
- SDKs: Python, Node.js, PHP (month 9+).

### 10.1 Third-Party Integrations

- **Payment:** Razorpay, Stripe, Cashfree, UPI AutoPay, eNACH.
- **Notifications:** MSG91, Twilio, SendGrid, AWS SES, WhatsApp Business API.
- **Accounting:** Zoho Books, Tally, QuickBooks (push invoices/payments).
- **Identity:** DigiLocker (Aadhaar e-KYC), Google, Apple, Okta/Azure AD SSO.
- **Analytics:** Mixpanel for product analytics, Segment as CDP.
- **Support:** Intercom for in-app chat, Zendesk for ticketing.
- **Storage:** AWS S3 primary, Cloudflare R2 for cost-optimized egress.

---

## 11. Engineering Team Structure

Scale requires team structure. Proposed org after 18 months:

| Team                  | Headcount | Owns                                                    |
| --------------------- | --------- | ------------------------------------------------------- |
| Platform / Infra      | 3–4       | Kubernetes, CI/CD, observability, security, DB          |
| Identity & Access     | 2–3       | Auth, RBAC, SSO, MFA, audit                             |
| Billing & Payments    | 4–5       | Billing engine, payment gateways, reconciliation, taxes |
| Notifications & Comms | 2–3       | Multi-channel delivery, templating, deliverability      |
| Tenant Experience     | 3–4       | Tenant app, meter readings, tickets, document vault     |
| Landlord Experience   | 3–4       | Landlord dashboard, reports, bulk ops, PMC workflows    |
| Data & Analytics      | 2–3       | Warehouse, BI, ML for anomaly detection                 |
| SRE / On-call         | 2         | Incident response, runbooks, DR drills                  |
| QA / Automation       | 2         | E2E tests, load testing, chaos engineering              |

---

## 12. Phased Rollout Plan

| Phase                             | Timeline    | Milestones                                                                                                                 |
| --------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Phase 0: Foundation**           | Month 1–2   | IaC, CI/CD, Kubernetes, Postgres, Redis, observability stack, auth service, organizations model, multi-tenancy enforcement |
| **Phase 1: MVP**                  | Month 2–3   | Properties, units, leases, tenant invite, rent billing, basic notifications (email), manual payment recording              |
| **Phase 2: Meter + SMS**          | Month 3–4   | Electricity module, photo upload, SMS via MSG91, notification preferences, in-app feed                                     |
| **Phase 3: Payments**             | Month 4–5   | Razorpay integration, auto-reconciliation, receipts, UPI AutoPay, refunds                                                  |
| **Phase 4: Scale Hardening**      | Month 5–6   | Load testing to 10K concurrent users, partition critical tables, read replicas, CDN, WAF, SOC 2 prep                       |
| **Phase 5: PMC Features**         | Month 6–8   | Bulk operations, multi-property dashboards, roles/permissions, API for PMCs, webhooks                                      |
| **Phase 6: Enterprise**           | Month 8–12  | SSO, dedicated tier, custom SLAs, white-labeling, audit exports, SOC 2 Type II                                             |
| **Phase 7: Geographic Expansion** | Month 12–18 | Multi-region active-active, SEA/ME localization, multi-currency, VAT engine                                                |
| **Phase 8: Platform**             | Month 18–24 | Public API marketplace, third-party app ecosystem, AI copilot for landlords                                                |

---

## 13. Cost Model & Unit Economics

### 13.1 Infrastructure Cost per 1K Active Tenants (Estimated)

| Item                                      | Monthly Cost                               |
| ----------------------------------------- | ------------------------------------------ |
| Compute (EKS)                             | ~$30                                       |
| Database (RDS Postgres multi-AZ)          | ~$40                                       |
| Cache (Redis)                             | ~$15                                       |
| Storage (S3 + CDN)                        | ~$10                                       |
| Observability (logs + metrics + traces)   | ~$20                                       |
| Notifications (avg 15 sends/tenant/month) | ~$60                                       |
| **Total fixed infra**                     | **~$175 / 1K tenants**                     |
| **Per tenant**                            | **$0.175 (infra) + $0.06 (notifications)** |

Payment gateway fees (~2% of GMV) are pass-through, not infra.

### 13.2 Pricing Strategy

- **Free tier:** up to 2 units, 1 landlord, basic features. Growth lever.
- **Pro:** ₹49/unit/month — SMS, payments, reports. Target solo landlords.
- **Business:** ₹99/unit/month — API, bulk ops, priority support. Target small PMCs.
- **Enterprise:** custom pricing, dedicated tier, SSO, SLAs. Target large PMCs.
- Optional 1% payment convenience fee on auto-pay transactions (landlord or tenant choice).

---

## 14. Risks at Scale

- **Notification cost explosion.** _Mitigation:_ smart channel selection, quiet hours, in-app first, SMS only for critical events.
- **Multi-tenant data leak.** _Mitigation:_ RLS at DB layer, automated tests for tenant isolation in every PR, pen tests.
- **Database hot-spotting on large PMCs.** _Mitigation:_ identify top 1% tenants early, move to Business/Enterprise tier with dedicated resources.
- **Payment gateway failure.** _Mitigation:_ multi-gateway routing, manual reconciliation fallback, clear customer comms.
- **Regulatory shifts (DPDP, rent control).** _Mitigation:_ modular compliance layer, legal advisor on retainer, quarterly review.
- **Talent scaling.** _Mitigation:_ hire platform + SRE early (month 4+), invest in docs + onboarding.
- **Migration pain at 10M+ users.** _Mitigation:_ design for sharding from day one (`organization_id` in every key), test partition splits quarterly.

---

## 15. Decisions to Make in Walkthrough

- [ ] Monolith-first (recommended) vs. microservices from day one?
- [ ] Cloud provider: AWS (most services, highest cost) vs. GCP vs. mix?
- [ ] Self-host Kafka/Postgres vs. fully managed (Aiven, Confluent Cloud)?
- [ ] Feature flag tool: LaunchDarkly (paid) vs. self-hosted Unleash?
- [ ] India-only for year 1, or SEA-ready architecture from the start?
- [ ] Are we chasing SOC 2 from month 1 (costly) or month 12 (blocks Enterprise deals)?
- [ ] AI features (from v1 PRD) — do we bundle into core or spin off as separate 'RentTrack Copilot' product?
- [ ] Hiring plan — how fast can we actually grow the team?

---

_End of document. Raise issues or comments directly on this file._
