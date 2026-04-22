import { test, expect } from '@playwright/test';
import { mockApi, seedAuth, MOCK_BILLS, MOCK_LEASES } from './helpers';

test.beforeEach(async ({ page }) => {
  await seedAuth(page);
});

function mockBillingApis(page: any, bills = MOCK_BILLS) {
  return Promise.all([
    mockApi(page, 'GET', '/billing/bills/', bills),
    mockApi(page, 'GET', '/properties/leases/', MOCK_LEASES),
  ]);
}

test.describe('BillingPage — rendering', () => {
  test('shows page heading and bill count', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await expect(page.getByRole('heading', { name: /billing/i })).toBeVisible();
    await expect(page.getByText(/3 bills/i)).toBeVisible();
  });

  test('renders bills table with correct columns', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Bill #' })).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Tenant' })).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Amount' })).toBeVisible();
    await expect(table.getByRole('columnheader', { name: 'Status' })).toBeVisible();
  });

  test('displays all three mock bills', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await expect(page.getByText('RT-2026-0001')).toBeVisible();
    await expect(page.getByText('RT-2026-0002')).toBeVisible();
    await expect(page.getByText('RT-2026-0003')).toBeVisible();
  });

  test('shows empty state when no bills', async ({ page }) => {
    await mockBillingApis(page, { count: 0, next: null, previous: null, results: [] });
    await page.goto('/billing');
    await expect(page.getByText(/no bills found/i)).toBeVisible();
  });
});

test.describe('BillingPage — status tabs', () => {
  test('clicking Overdue tab updates URL param', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await page.getByRole('button', { name: /overdue/i }).click();
    await expect(page).toHaveURL(/status=overdue/);
  });

  test('clicking Paid tab updates URL param', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await page.getByRole('button', { name: /^paid$/i }).click();
    await expect(page).toHaveURL(/status=paid/);
  });

  test('clicking All tab clears status param', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing?status=overdue');
    await page.getByRole('button', { name: /^all$/i }).click();
    // URL should not contain status=overdue any more
    const url = page.url();
    expect(url).not.toContain('status=overdue');
  });
});

test.describe('BillingPage — search filter', () => {
  test('typing in search updates URL after debounce', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await page.getByPlaceholder(/search tenant, bill number/i).fill('RT-2026-0001');
    // Wait for debounce (400ms) + navigation
    await page.waitForTimeout(600);
    await expect(page).toHaveURL(/search=RT-2026-0001/);
  });

  test('clear filters button resets search and status', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing?status=overdue&search=test');
    // Clear filters button should be visible when params are set
    await expect(page.getByRole('button', { name: /clear filters/i })).toBeVisible();
    await page.getByRole('button', { name: /clear filters/i }).click();
    await expect(page).toHaveURL(/\/billing(\?page=1)?$/);
  });
});

test.describe('BillingPage — date range filter', () => {
  test('setting due-date from updates URL', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    // Find the "Due from" date input
    const fromInput = page.locator('input[type="date"]').first();
    await fromInput.fill('2026-04-01');
    await expect(page).toHaveURL(/due_date__gte=2026-04-01/);
  });

  test('setting due-date to updates URL', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    const toInput = page.locator('input[type="date"]').last();
    await toInput.fill('2026-04-30');
    await expect(page).toHaveURL(/due_date__lte=2026-04-30/);
  });
});

test.describe('BillingPage — pagination', () => {
  test('shows pagination when count > page_size', async ({ page }) => {
    // Simulate 30 results (page size is 25)
    const bigResponse = {
      count: 30,
      next: 'http://localhost:8000/api/v1/billing/bills/?page=2',
      previous: null,
      results: MOCK_BILLS.results,
    };
    await mockBillingApis(page, bigResponse);
    await page.goto('/billing');
    await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
    await expect(page.getByText(/showing.*of 30/i)).toBeVisible();
  });

  test('does not show pagination when results fit on one page', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await expect(page.getByRole('button', { name: /^next$/i })).not.toBeVisible();
  });

  test('clicking Next updates page param', async ({ page }) => {
    const bigResponse = {
      count: 30,
      next: 'http://localhost:8000/api/v1/billing/bills/?page=2',
      previous: null,
      results: MOCK_BILLS.results,
    };
    await mockBillingApis(page, bigResponse);
    await page.goto('/billing');
    await page.getByRole('button', { name: /next/i }).click();
    await expect(page).toHaveURL(/page=2/);
  });
});

test.describe('BillingPage — generate bill modal', () => {
  test('opens generate bill modal on button click', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await page.getByRole('button', { name: /\+ generate bill/i }).click();
    await expect(page.getByRole('dialog', { name: /generate rent bill/i })).toBeVisible();
  });

  test('modal closes on Cancel', async ({ page }) => {
    await mockBillingApis(page);
    await page.goto('/billing');
    await page.getByRole('button', { name: /\+ generate bill/i }).click();
    await page.getByRole('button', { name: /cancel/i }).click();
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });
});
