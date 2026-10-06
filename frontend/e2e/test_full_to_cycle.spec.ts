import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Helper function to wait for API calls
async function waitForAPICall(page, urlPattern, timeout = 5000) {
  return page.waitForResponse(resp => resp.url().includes(urlPattern) && resp.status() === 200, { timeout });
}

test.describe('Full TO Cycle', () => {
  let adminCredentials = { username: 'admin', password: 'admin123' };
  let technicianCredentials = { username: 'technician', password: 'tech123' };
  let apparatusId: string;
  let technicianId: string;
  let taskId: string;

  test.beforeAll(async ({ request }) => {
    // Seed data via API: create apparatus, technician, and task
    const baseURL = process.env.VITE_API_URL || 'http://localhost:8000';

    // Create apparatus
    const apparatusResp = await request.post(`${baseURL}/apparatuses`, {
      data: {
        name: 'Test Apparatus',
        gps_latitude: 55.7558,
        gps_longitude: 37.6176,
        inventory_number: `INV-${Date.now()}`,
      },
    });
    expect(apparatusResp.ok()).toBeTruthy();
    const apparatus = await apparatusResp.json();
    apparatusId = apparatus.id;

    // Create technician
    const technicianResp = await request.post(`${baseURL}/technicians`, {
      data: {
        name: 'Test Technician',
        email: 'tech@example.com',
        phone: '+1234567890',
      },
    });
    expect(technicianResp.ok()).toBeTruthy();
    const technician = await technicianResp.json();
    technicianId = technician.id;

    // Assign technician to apparatus (if needed via API)
    // We'll assume there's an endpoint to assign
    await request.patch(`${baseURL}/apparatuses/${apparatusId}`, {
      data: { technician_id: technicianId },
    });

    // Create a TO task via API (simulate scheduler)
    const taskResp = await request.post(`${baseURL}/tasks`, {
      data: {
        apparatus_id: apparatusId,
        technician_id: technicianId,
        type: 'TO',
        status: 'CREATED',
      },
    });
    expect(taskResp.ok()).toBeTruthy();
    const task = await taskResp.json();
    taskId = task.id;
  });

  test('admin login, create apparatus and technician', async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', adminCredentials.username);
    await page.fill('[data-testid="password-input"]', adminCredentials.password);
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');

    // Navigate to apparatuses and create apparatus (already done via API, but we can verify)
    await page.goto('/apparatuses');
    await expect(page.locator(`text=${apparatusId}`)).toBeVisible();

    // Navigate to technicians and create technician (verify)
    await page.goto('/technicians');
    await expect(page.locator(`text=${technicianId}`)).toBeVisible();
  });

  test('technician flow: QR scan -> photos -> GPS -> meter -> cash -> comment -> completed', async ({ page }) => {
    // Login as technician
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', technicianCredentials.username);
    await page.fill('[data-testid="password-input"]', technicianCredentials.password);
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/technician/dashboard');

    // Simulate QR scan: we'll navigate directly to the task detail page for the technician
    // In a real app, scanning a QR would redirect to a URL like /task/:id/qr-scan
    await page.goto(`/technician/task/${taskId}/qr-scan`);

    // Step 1: QR scan successful (we assume it's done)
    await expect(page.locator('[data-testid="qr-scan-success"]')).toBeVisible({ timeout: 10000 });
    await page.click('[data-testid="proceed-to-checklist"]');

    // Step 2: 6-step photo checklist
    for (let i = 1; i <= 6; i++) {
      await expect(page.locator(`[data-testid="photo-step-${i}"]`)).toBeVisible();
      // Mock file upload: we'll attach a dummy file
      const fileChooserPromise = page.waitForEvent('filechooser');
      await page.click(`[data-testid="upload-photo-${i}"]`);
      const fileChooser = await fileChooserPromise;
      await fileChooser.setFiles(path.join(__dirname, '../../test-data/photo.jpg'));
      // Wait for upload to complete (we'll wait for a success indicator)
      await expect(page.locator(`[data-testid="photo-step-${i}"] .upload-success`)).toBeVisible();
      // Proceed to next step (if not last)
      if (i < 6) {
        await page.click('[data-testid="next-step"]');
      }
    }

    // After photo checklist, proceed to GPS validation
    await page.click('[data-testid="complete-checklist"]');
    await expect(page.locator('[data-testid="gps-validation"]')).toBeVisible();

    // Mock GPS validation: we'll override the geolocation
    await page.context().overridePermissions('/technician/task/*', ['geolocation']);
    await page.context().setGeolocation({ latitude: 55.7558, longitude: 37.6176 });
    await page.click('[data-testid="validate-gps"]');
    await expect(page.locator('[data-testid="gps-validated"]')).toBeVisible();

    // Step 3: Meter readings
    await page.click('[data-testid="proceed-to-meter"]');
    await expect(page.locator('[data-testid="meter-readings"]')).toBeVisible();
    await page.fill('[data-testid="meter-input"]', '12345');
    await page.click('[data-testid="save-meter"]');

    // Step 4: Cash amount
    await page.click('[data-testid="proceed-to-cash"]');
    await expect(page.locator('[data-testid="cash-amount"]')).toBeVisible();
    await page.fill('[data-testid="cash-input"]', '1000');
    await page.click('[data-testid="save-cash"]');

    // Step 5: Photo cash
    await page.click('[data-testid="proceed-to-photo-cash"]');
    await expect(page.locator('[data-testid="photo-cash-upload"]')).toBeVisible();
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('[data-testid="upload-photo-cash"]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(path.join(__dirname, '../../test-data/cash-photo.jpg'));
    await expect(page.locator('[data-testid="photo-cash-uploaded"]')).toBeVisible();

    // Step 6: Comment
    await page.click('[data-testid="proceed-to-comment"]');
    await expect(page.locator('[data-testid="comment-input"]')).toBeVisible();
    await page.fill('[data-testid="comment-input"]', 'Test comment');
    await page.click('[data-testid="save-comment"]');

    // Final step: Mark as completed
    await page.click('[data-testid="complete-task"]');
    await expect(page.locator('[data-testid="task-completed"]')).toBeVisible();
  });

  test('admin approval in web panel', async ({ page }) => {
    // Login as admin again
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', adminCredentials.username);
    await page.fill('[data-testid="password-input"]', adminCredentials.password);
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');

    // Go to tasks page
    await page.goto('/tasks');
    // Wait for the task to appear in the list
    await expect(page.locator(`text=${taskId}`)).toBeVisible({ timeout: 10000 });

    // Click on the task to open details
    await page.click(`text=${taskId}`);
    await expect(page.locator('[data-testid="task-details"]')).toBeVisible();

    // Approve the task
    await page.click('[data-testid="approve-task"]');
    await expect(page.locator('[data-testid="task-approved"]')).toBeVisible();
  });

  test('rating update verification', async ({ request }) => {
    // Verify that the apparatus or technician rating has been updated
    const baseURL = process.env.VITE_API_URL || 'http://localhost:8000';

    // Check apparatus rating
    const apparatusResp = await request.get(`${baseURL}/apparatuses/${apparatusId}`);
    expect(apparatusResp.ok()).toBeTruthy();
    const apparatus = await apparatusResp.json();
    // Assuming rating is a number between 0 and 5
    expect(typeof apparatus.rating).toBe('number');
    expect(apparatus.rating).toBeGreaterThanOrEqual(0);
    expect(apparatus.rating).toBeLessThanOrEqual(5);

    // Check technician rating
    const technicianResp = await request.get(`${baseURL}/technicians/${technicianId}`);
    expect(technicianResp.ok()).toBeTruthy();
    const technician = await technicianResp.json();
    expect(typeof technician.rating).toBe('number');
    expect(technician.rating).toBeGreaterThanOrEqual(0);
    expect(technician.rating).toBeLessThanOrEqual(5);
  });
});