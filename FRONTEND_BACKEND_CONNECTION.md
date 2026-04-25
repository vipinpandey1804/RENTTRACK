# RentTrack — Frontend ↔ Backend Connection Guide

## Overview

| Layer      | Technology                   | Dev URL                 |
| ---------- | ---------------------------- | ----------------------- |
| Frontend   | React 18 + Vite + TypeScript | `http://localhost:5173` |
| Backend    | Django 5.2 + DRF             | `http://localhost:8000` |
| Database   | PostgreSQL                   | `localhost:5432`        |
| Cache      | Redis                        | `localhost:6379`        |
| Task queue | Django Q2 (ORM broker)       | runs via `qcluster`     |

---

## 1. Running the Stack

### Backend

```bash
# From E:\RENTTRACK\backend
# Activate virtual environment
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# Start Django dev server
python manage.py runserver

# Start background task worker (separate terminal)
python manage.py qcluster
```

### Frontend

```bash
# From E:\RENTTRACK\frontend
npm install
npm run dev       # http://localhost:5173
```

### Environment variables

Copy `.env.example` (or create `.env` at project root `E:\RENTTRACK\.env`):

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://user:pass@localhost:5432/renttrack
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:5173
FRONTEND_URL=http://localhost:5173
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30
```

---

## 2. CORS Configuration

The backend allows cross-origin requests from the frontend via `django-cors-headers`.

In `config/settings/base.py`:

```python
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")   # ["http://localhost:5173"]
CORS_ALLOW_CREDENTIALS = True
```

Set `CORS_ALLOWED_ORIGINS=http://localhost:5173` in `.env` for local dev.
In production, set it to your deployed frontend domain (e.g., `https://app.renttrack.com`).

---

## 3. Authentication Flow (JWT)

The backend uses **SimpleJWT**. Every protected API call requires an `Authorization` header.

### Login

```
POST /api/v1/auth/login/
Content-Type: application/json

{ "email": "user@example.com", "password": "secret" }
```

Response:

```json
{ "access": "<jwt-access-token>", "refresh": "<jwt-refresh-token>" }
```

Store tokens in memory (or `localStorage` as a fallback). **Do not store in cookies** unless you configure `httpOnly` cookies on the backend.

### Making authenticated requests

```typescript
// axios instance — src/lib/api.ts (suggested pattern)
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

### Refresh token

```
POST /api/v1/auth/refresh/
{ "refresh": "<jwt-refresh-token>" }
```

Returns a new `access` token. Add an Axios response interceptor to call this automatically on `401` errors.

### Logout

```
POST /api/v1/auth/logout/
Authorization: Bearer <access-token>
{ "refresh": "<jwt-refresh-token>" }
```

Blacklists the refresh token server-side.

---

## 4. API Endpoints Reference

All endpoints are prefixed with `/api/v1/`.

### Auth — `/api/v1/auth/`

| Method | Path                   | Description                        |
| ------ | ---------------------- | ---------------------------------- |
| POST   | `login/`               | Obtain JWT access + refresh tokens |
| POST   | `refresh/`             | Refresh access token               |
| POST   | `signup/`              | Register new user + organization   |
| POST   | `logout/`              | Blacklist refresh token            |
| GET    | `me/`                  | Current user profile               |
| PATCH  | `me/`                  | Update profile                     |
| POST   | `me/change-password/`  | Change password                    |
| POST   | `verify-email/`        | Verify email with token            |
| POST   | `resend-verification/` | Resend verification email          |
| POST   | `invite/`              | Send member invite                 |
| GET    | `invite/<token>/`      | Validate invite token              |
| POST   | `accept-invite/`       | Accept invite and join org         |
| GET    | `members/`             | List org members                   |
| POST   | `switch-org/`          | Switch active organization         |

### Properties — `/api/v1/properties/`

| Method | Path                              | Description     |
| ------ | --------------------------------- | --------------- |
| GET    | `/api/v1/properties/`             | List properties |
| POST   | `/api/v1/properties/`             | Create property |
| GET    | `/api/v1/properties/<id>/`        | Get property    |
| PATCH  | `/api/v1/properties/<id>/`        | Update property |
| GET    | `/api/v1/properties/units/`       | List units      |
| POST   | `/api/v1/properties/units/`       | Create unit     |
| GET    | `/api/v1/properties/units/<id>/`  | Get unit        |
| GET    | `/api/v1/properties/leases/`      | List leases     |
| POST   | `/api/v1/properties/leases/`      | Create lease    |
| GET    | `/api/v1/properties/leases/<id>/` | Get lease       |

### Billing — `/api/v1/billing/`

| Method | Path                         | Description                     |
| ------ | ---------------------------- | ------------------------------- |
| GET    | `bills/`                     | List bills (filterable)         |
| GET    | `bills/<id>/`                | Get bill detail                 |
| POST   | `bills/generate/`            | Manually generate a bill        |
| POST   | `bills/<id>/record-payment/` | Record a payment against a bill |
| POST   | `bills/<id>/cancel/`         | Cancel a bill                   |

### Payments — `/api/v1/payments/`

| Method | Path                     | Description        |
| ------ | ------------------------ | ------------------ |
| GET    | `/api/v1/payments/`      | List payments      |
| GET    | `/api/v1/payments/<id>/` | Get payment detail |

### Notifications — `/api/v1/notifications/`

| Method | Path                          | Description        |
| ------ | ----------------------------- | ------------------ |
| GET    | `/api/v1/notifications/`      | List notifications |
| GET    | `/api/v1/notifications/<id>/` | Get notification   |

### Health — `/health/`

```
GET /health/    → { "status": "ok" }
```

---

## 5. API Documentation (Swagger / ReDoc)

The backend auto-generates OpenAPI 3.0 docs via `drf-spectacular`.

| URL                                 | Description           |
| ----------------------------------- | --------------------- |
| `http://localhost:8000/api/schema/` | Raw OpenAPI JSON/YAML |
| `http://localhost:8000/api/docs/`   | Swagger UI            |
| `http://localhost:8000/api/redoc/`  | ReDoc UI              |

Use the Swagger UI to explore request/response shapes, test endpoints interactively, and copy the exact field names for TypeScript types.

---

## 6. Connecting with React Query + Axios (Recommended Pattern)

### Setup — `src/lib/api.ts`

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        const { data } = await axios.post("/api/v1/auth/refresh/", { refresh });
        localStorage.setItem("access_token", data.access);
        err.config.headers.Authorization = `Bearer ${data.access}`;
        return api(err.config);
      }
    }
    return Promise.reject(err);
  },
);
```

### Environment variable — `frontend/.env.local`

```env
VITE_API_URL=http://localhost:8000
```

### Example query — fetching bills

```typescript
// src/hooks/useBills.ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useBills(filters?: { status?: string }) {
  return useQuery({
    queryKey: ["bills", filters],
    queryFn: () =>
      api
        .get("/api/v1/billing/bills/", { params: filters })
        .then((r) => r.data),
  });
}
```

### Example mutation — recording a payment

```typescript
// src/hooks/useRecordPayment.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useRecordPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ billId, amount }: { billId: string; amount: number }) =>
      api.post(`/api/v1/billing/bills/${billId}/record-payment/`, { amount }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["bills"] }),
  });
}
```

---

## 7. Pagination

List endpoints return paginated responses (25 items per page by default):

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/billing/bills/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Pass `?page=2` to fetch the next page.

---

## 8. Filtering, Search, and Ordering

Most list endpoints support:

| Query param          | Example               | Description                        |
| -------------------- | --------------------- | ---------------------------------- |
| `search`             | `?search=john`        | Full-text search on indexed fields |
| `ordering`           | `?ordering=-due_date` | Sort (prefix `-` for descending)   |
| Status/field filters | `?status=overdue`     | Exact filter on filterable fields  |

---

## 9. Error Response Shape

```json
{
  "detail": "Authentication credentials were not provided."
}
```

or for validation errors:

```json
{
  "amount": ["This field is required."],
  "lease_id": ["Invalid pk."]
}
```

Handle both shapes in your API error handler.

---

## 10. Background Tasks (Django Q2)

The following tasks run asynchronously via `python manage.py qcluster`:

| Task                      | Trigger                  | Description                  |
| ------------------------- | ------------------------ | ---------------------------- |
| `notify_bill_issued`      | On bill creation         | Sends email to tenant        |
| `notify_payment_received` | On payment recorded      | Sends receipt email          |
| `dispatch_notification`   | On notification enqueued | Generic email dispatch       |
| `generate_daily_bills`    | Cron — 06:00 IST         | Auto-generate rent bills     |
| `mark_overdue_bills_task` | Cron — 00:05 IST         | Mark unpaid bills as overdue |

In development you can skip running `qcluster`; task calls are non-blocking and fail silently if the queue is not consumed.

---

## 11. Admin Panel

```
http://localhost:8000/admin/
```

Create a superuser first:

```bash
python manage.py createsuperuser
```

The admin panel lets you inspect Django Q task results, scheduled jobs, and all app data.
