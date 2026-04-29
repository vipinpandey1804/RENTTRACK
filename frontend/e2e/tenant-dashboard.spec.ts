import { test, expect } from "@playwright/test";
import {
  mockApi,
  seedAuth,
  seedTenantAuth,
  MOCK_BILLS,
  MOCK_LEASES,
} from "./helpers";

function mockTenantApis(page: any) {
  return Promise.all([
    mockApi(page, "GET", "/properties/leases/", MOCK_LEASES),
    mockApi(page, "GET", "/billing/bills/", MOCK_BILLS),
  ]);
}

test.describe("Tenant Dashboard — routing", () => {
  test("owner role sees landlord DashboardPage (not TenantDashboard)", async ({
    page,
  }) => {
    await seedAuth(page);
    await mockApi(page, "GET", "/properties/", {
      count: 0,
      results: [],
      next: null,
      previous: null,
    });
    await mockApi(page, "GET", "/billing/bills/", {
      count: 0,
      results: [],
      next: null,
      previous: null,
    });
    await page.goto("/dashboard");
    // Landlord dashboard shows Properties or summary — NOT "Your Tenancy"
    await expect(page.getByText(/your tenancy/i)).not.toBeVisible({
      timeout: 3000,
    });
  });

  test("tenant role is routed to TenantDashboardPage", async ({ page }) => {
    await seedTenantAuth(page);
    await mockTenantApis(page);
    await page.goto("/dashboard");
    await expect(page.getByText(/your tenancy/i)).toBeVisible({
      timeout: 5000,
    });
  });
});

test.describe("Tenant Dashboard — content", () => {
  test.beforeEach(async ({ page }) => {
    await seedTenantAuth(page);
    await mockTenantApis(page);
    await page.goto("/dashboard");
  });

  test("shows welcome greeting with user first name", async ({ page }) => {
    await expect(page.getByText(/welcome back, test/i)).toBeVisible();
  });

  test("shows email not verified banner for unverified tenant", async ({
    page,
  }) => {
    await expect(page.getByText(/email not verified/i)).toBeVisible();
  });

  test("shows active lease card", async ({ page }) => {
    await expect(page.getByText("Flat 3B")).toBeVisible();
    await expect(page.getByText("Sunrise Apts")).toBeVisible();
    await expect(
      page.getByRole("definition").filter({ hasText: "₹15,000" }),
    ).toBeVisible();
  });

  test("shows lease dates", async ({ page }) => {
    await expect(page.getByText(/01 Jan 2026/i)).toBeVisible();
  });

  test("shows outstanding bills section heading", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: /outstanding bills/i }),
    ).toBeVisible();
  });

  test("overdue bill appears in outstanding table", async ({ page }) => {
    await expect(
      page.getByRole("link", { name: "RT-2026-0003" }).first(),
    ).toBeVisible();
  });

  test("issued bill appears in outstanding table", async ({ page }) => {
    await expect(
      page.getByRole("link", { name: "RT-2026-0001" }).first(),
    ).toBeVisible();
  });

  test("paid bill does NOT appear in outstanding table", async ({ page }) => {
    // RT-2026-0002 is paid — the mock /billing/bills/ returns all 3 bills but the
    // dashboard fetches issued+overdue separately; RT-2026-0002 won't be in those.
    // Scope check to the outstanding table only.
    const outstandingTable = page.locator("table").first();
    await expect(
      outstandingTable.getByRole("link", { name: "RT-2026-0002" }),
    ).not.toBeVisible({ timeout: 3000 });
  });

  test("shows View all bills link", async ({ page }) => {
    const link = page.getByRole("link", { name: /view all bills/i });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/billing");
  });

  test("shows account info section", async ({ page }) => {
    await expect(page.getByText("tenant@test.com")).toBeVisible();
  });

  test("all caught up state shown when no outstanding bills", async ({
    page,
  }) => {
    await mockApi(page, "GET", "/billing/bills/", {
      count: 0,
      results: [],
      next: null,
      previous: null,
    });
    await page.reload();
    await expect(page.getByText(/all caught up/i)).toBeVisible({
      timeout: 5000,
    });
  });
});

test.describe("Tenant Dashboard — no active lease", () => {
  test("shows no active lease message", async ({ page }) => {
    await seedTenantAuth(page);
    await mockApi(page, "GET", "/properties/leases/", {
      count: 0,
      results: [],
      next: null,
      previous: null,
    });
    await mockApi(page, "GET", "/billing/bills/", {
      count: 0,
      results: [],
      next: null,
      previous: null,
    });
    await page.goto("/dashboard");
    await expect(page.getByText(/no active lease found/i)).toBeVisible({
      timeout: 5000,
    });
  });
});
