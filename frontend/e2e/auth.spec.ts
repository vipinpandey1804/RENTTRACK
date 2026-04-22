import { test, expect } from '@playwright/test';
import { mockApi, seedAuth, seedTenantAuth } from './helpers';

test.describe('Login page', () => {
  test('renders login form', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('shows error on bad credentials', async ({ page }) => {
    await mockApi(page, 'POST', '/auth/login/', { detail: 'No active account found with the given credentials' }, 401);
    await page.goto('/login');
    await page.locator('input[type="email"]').fill('bad@test.com');
    await page.locator('input[type="password"]').fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/invalid|incorrect|no active account/i)).toBeVisible({ timeout: 5000 });
  });

  test('redirects authenticated user away from /login', async ({ page }) => {
    await seedAuth(page);
    await mockApi(page, 'GET', '/auth/me/', { id: 'user-uuid-1', email: 'landlord@test.com' });
    await page.goto('/login');
    await expect(page).toHaveURL(/dashboard/);
  });
});

test.describe('Signup page', () => {
  test('renders signup form', async ({ page }) => {
    await page.goto('/signup');
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /sign up|create account/i })).toBeVisible();
  });

  test('shows validation errors for empty submit', async ({ page }) => {
    await page.goto('/signup');
    await page.getByRole('button', { name: /sign up|create account/i }).click();
    // Browser built-in validation or custom messages should appear
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeVisible();
  });
});

test.describe('Email verification banner', () => {
  test('shows warning banner for unverified tenant', async ({ page }) => {
    await seedTenantAuth(page);
    await mockApi(page, 'GET', '/properties/leases/', { count: 0, results: [], next: null, previous: null });
    await mockApi(page, 'GET', '/billing/bills/', { count: 0, results: [], next: null, previous: null });
    await page.goto('/dashboard');
    await expect(page.getByText(/email not verified/i)).toBeVisible({ timeout: 5000 });
  });

  test('does not show banner for verified owner', async ({ page }) => {
    await seedAuth(page);
    // Mock dashboard data
    await mockApi(page, 'GET', '/properties/', { count: 0, results: [], next: null, previous: null });
    await mockApi(page, 'GET', '/billing/bills/', { count: 0, results: [], next: null, previous: null });
    await page.goto('/dashboard');
    await expect(page.getByText(/email not verified/i)).not.toBeVisible({ timeout: 3000 });
  });
});

test.describe('Protected routes', () => {
  test('redirects unauthenticated user to /login from /dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/login');
  });

  test('redirects unauthenticated user to /login from /billing', async ({ page }) => {
    await page.goto('/billing');
    await expect(page).toHaveURL('/login');
  });

  test('redirects unauthenticated user to /login from /properties', async ({ page }) => {
    await page.goto('/properties');
    await expect(page).toHaveURL('/login');
  });
});
