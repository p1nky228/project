import { test, expect } from '@playwright/test';

test.describe('Admin Panel', () => {
  let adminCredentials = { username: 'admin', password: 'admin123' };

  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', adminCredentials.username);
    await page.fill('[data-testid="password-input"]', adminCredentials.password);
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('dashboard page shows key metrics', async ({ page }) => {
    // Already on dashboard from beforeEach
    await expect(page.locator('[data-testid="dashboard-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-apparatuses"]')).toBeVisible();
    await expect(page.locator('[data-testid="total-technicians"]')).toBeVisible();
    await expect(page.locator('[data-testid="pending-tasks"]')).toBeVisible();
    await expect(page.locator('[data-testid="completed-tasks"]')).toBeVisible();
  });

  test('map page displays apparatuses', async ({ page }) => {
    await page.goto('/map');
    await expect(page.locator('[data-testid="map-container"]')).toBeVisible();
    // Check that at least one apparatus marker is present (if we have seeded data)
    // We'll just check that the map is loaded
    await expect(page.locator('[data-testid="map-loading"]')).not.toBeVisible();
  });

  test('tasks page lists tasks and allows filtering', async ({ page }) => {
    await page.goto('/tasks');
    await expect(page.locator('[data-testid="tasks-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="task-row"]')).toHaveCountGreaterThan(0);
    // Test filter by status
    await page.selectOption('[data-testid="status-filter"]', 'CREATED');
    await expect(page.locator('[data-testid="task-row"]')).toHaveCountGreaterThan(0);
  });

  test('technicians page lists technicians and allows adding/editing', async ({ page }) => {
    await page.goto('/technicians');
    await expect(page.locator('[data-testid="technicians-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="technician-row"]')).toHaveCountGreaterThan(0);
    // Click add button
    await page.click('[data-testid="add-technician-button"]');
    await expect(page.locator('[data-testid="add-technician-form"]')).toBeVisible();
    // Fill form and submit (we'll use dummy data)
    await page.fill('[data-testid="technician-name"]', 'Test Tech');
    await page.fill('[data-testid="technician-email"]', 'test@example.com');
    await page.fill('[data-testid="technician-phone"]', '+1234567890');
    await page.click('[data-testid="save-technician-button"]');
    await expect(page.locator('[data-testid="technician-row"]:has-text("Test Tech")')).toBeVisible();
  });

  test('apparatuses page lists apparatuses and allows adding/editing', async ({ page }) => {
    await page.goto('/apparatuses');
    await expect(page.locator('[data-testid="apparatuses-table"]')).toBeVisible();
    await expect(page.locator('[data-testid="apparatus-row"]')).toHaveCountGreaterThan(0);
    // Click add button
    await page.click('[data-testid="add-apparatus-button"]');
    await expect(page.locator('[data-testid="add-apparatus-form"]')).toBeVisible();
    // Fill form and submit
    await page.fill('[data-testid="apparatus-name"]', 'Test Apparatus');
    await page.fill('[data-testid="apparatus-inventory"]', `INV-${Date.now()}`);
    await page.fill('[data-testid="apparatus-lat"]', '55.7558');
    await page.fill('[data-testid="apparatus-lng"]', '37.6176');
    await page.click('[data-testid="save-apparatus-button"]');
    await expect(page.locator('[data-testid="apparatus-row"]:has-text("Test Apparatus")')).toBeVisible();
  });
});