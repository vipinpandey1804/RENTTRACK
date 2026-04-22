import { Page, expect } from '@playwright/test';

export const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';
export const API_URL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api/v1';

/** Intercept API with a mock response so tests never need a live backend. */
export async function mockApi(
  page: Page,
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
  urlPattern: string | RegExp,
  body: unknown,
  status = 200,
) {
  await page.route(
    typeof urlPattern === 'string'
      ? (url) => url.toString().includes(urlPattern)
      : urlPattern,
    (route) => {
      if (route.request().method() !== method) {
        route.fallback();
        return;
      }
      route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    },
  );
}

/** Seed localStorage with a valid auth token so pages don't redirect to /login. */
export async function seedAuth(page: Page, overrides: Record<string, unknown> = {}) {
  const user = {
    id: 'user-uuid-1',
    email: 'landlord@test.com',
    first_name: 'Test',
    last_name: 'Landlord',
    phone: '',
    phone_verified: false,
    email_verified: true,
    active_organization: {
      id: 'org-uuid-1',
      name: 'Test Org',
      slug: 'test-org',
      tier: 'shared',
      primary_email: 'landlord@test.com',
    },
    memberships: [
      {
        id: 'mem-uuid-1',
        organization: {
          id: 'org-uuid-1',
          name: 'Test Org',
          slug: 'test-org',
          tier: 'shared',
          primary_email: 'landlord@test.com',
        },
        role: 'owner',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
    ...overrides,
  };

  await page.addInitScript((u) => {
    const state = {
      state: {
        accessToken: 'mock-access-token',
        refreshToken: 'mock-refresh-token',
        user: u,
      },
      version: 0,
    };
    localStorage.setItem('renttrack-auth', JSON.stringify(state));
  }, user);
}

export async function seedTenantAuth(page: Page) {
  await seedAuth(page, {
    id: 'tenant-uuid-1',
    email: 'tenant@test.com',
    first_name: 'Test',
    last_name: 'Tenant',
    email_verified: false,
    active_organization: {
      id: 'org-uuid-1',
      name: 'Test Org',
      slug: 'test-org',
      tier: 'shared',
      primary_email: 'landlord@test.com',
    },
    memberships: [
      {
        id: 'mem-uuid-2',
        organization: {
          id: 'org-uuid-1',
          name: 'Test Org',
          slug: 'test-org',
          tier: 'shared',
          primary_email: 'landlord@test.com',
        },
        role: 'tenant',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  });
}

export const MOCK_BILLS = {
  count: 3,
  next: null,
  previous: null,
  results: [
    {
      id: 'bill-1',
      bill_number: 'RT-2026-0001',
      bill_type: 'rent',
      lease: 'lease-1',
      lease_info: {
        id: 'lease-1',
        tenant_email: 'tenant@test.com',
        tenant_name: 'Test Tenant',
        unit_name: 'Flat 3B',
        property_name: 'Sunrise Apts',
      },
      period_start: '2026-04-01',
      period_end: '2026-04-30',
      issue_date: '2026-04-01',
      due_date: '2026-04-10',
      subtotal: '15000.00',
      tax_amount: '0.00',
      total_amount: '15000.00',
      amount_paid: '0.00',
      balance_due: '15000.00',
      status: 'issued',
      line_items: [],
      payments: [],
      created_at: '2026-04-01T00:00:00Z',
      updated_at: '2026-04-01T00:00:00Z',
    },
    {
      id: 'bill-2',
      bill_number: 'RT-2026-0002',
      bill_type: 'rent',
      lease: 'lease-1',
      lease_info: {
        id: 'lease-1',
        tenant_email: 'tenant@test.com',
        tenant_name: 'Test Tenant',
        unit_name: 'Flat 3B',
        property_name: 'Sunrise Apts',
      },
      period_start: '2026-03-01',
      period_end: '2026-03-31',
      issue_date: '2026-03-01',
      due_date: '2026-03-10',
      subtotal: '15000.00',
      tax_amount: '0.00',
      total_amount: '15000.00',
      amount_paid: '15000.00',
      balance_due: '0.00',
      status: 'paid',
      line_items: [],
      payments: [],
      created_at: '2026-03-01T00:00:00Z',
      updated_at: '2026-03-15T00:00:00Z',
    },
    {
      id: 'bill-3',
      bill_number: 'RT-2026-0003',
      bill_type: 'rent',
      lease: 'lease-2',
      lease_info: {
        id: 'lease-2',
        tenant_email: 'tenant2@test.com',
        tenant_name: 'Second Tenant',
        unit_name: 'Shop 1',
        property_name: 'Main Street',
      },
      period_start: '2026-03-01',
      period_end: '2026-03-31',
      issue_date: '2026-03-01',
      due_date: '2026-03-05',
      subtotal: '20000.00',
      tax_amount: '0.00',
      total_amount: '20000.00',
      amount_paid: '0.00',
      balance_due: '20000.00',
      status: 'overdue',
      line_items: [],
      payments: [],
      created_at: '2026-03-01T00:00:00Z',
      updated_at: '2026-03-06T00:00:00Z',
    },
  ],
};

export const MOCK_LEASES = {
  count: 2,
  next: null,
  previous: null,
  results: [
    {
      id: 'lease-1',
      unit: 'unit-1',
      unit_name: 'Flat 3B',
      property_name: 'Sunrise Apts',
      tenant: 'tenant-uuid-1',
      tenant_email: 'tenant@test.com',
      start_date: '2026-01-01',
      end_date: null,
      monthly_rent: '15000.00',
      security_deposit_held: '30000.00',
      billing_cycle: 'monthly',
      billing_day_of_month: 1,
      grace_period_days: 5,
      late_fee_type: 'none',
      late_fee_value: '0.00',
      status: 'active',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    },
  ],
};
