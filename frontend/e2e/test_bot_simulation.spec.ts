import { test, expect } from '@playwright/test';

test.describe('Bot Simulation via API', () => {
  let baseURL: string;
  let apparatusId: string;
  let technicianId: string;
  let taskId: string;

  test.beforeAll(async ({ request }) => {
    baseURL = process.env.VITE_API_URL || 'http://localhost:8000';

    // Create apparatus
    const apparatusResp = await request.post(`${baseURL}/apparatuses`, {
      data: {
        name: 'Bot Test Apparatus',
        gps_latitude: 55.7558,
        gps_longitude: 37.6176,
        inventory_number: `BOT-INV-${Date.now()}`,
      },
    });
    expect(apparatusResp.ok()).toBeTruthy();
    const apparatus = await apparatusResp.json();
    apparatusId = apparatus.id;

    // Create technician
    const technicianResp = await request.post(`${baseURL}/technicians`, {
      data: {
        name: 'Bot Test Technician',
        email: 'bot@example.com',
        phone: '+1234567890',
      },
    });
    expect(technicianResp.ok()).toBeTruthy();
    const technician = await technicianResp.json();
    technicianId = technician.id;

    // Assign technician to apparatus
    await request.patch(`${baseURL}/apparatuses/${apparatusId}`, {
      data: { technician_id: technicianId },
    });
  });

  test('bot creates a TO task and updates it through stages', async ({ request }) => {
    // Step 1: Create a TO task
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

    // Step 2: Bot simulates QR scan (we'll update task status to SCANNED or similar)
    // Assuming there's an endpoint to update task status via QR scan
    const qrScanResp = await request.patch(`${baseURL}/tasks/${taskId}/qr-scan`, {
      data: { scanned_at: new Date().toISOString() },
    });
    expect(qrScanResp.ok()).toBeTruthy();

    // Step 3: Bot submits photo checklist (we'll update photos)
    // We'll simulate by updating a photos array or a checklist completed flag
    const photosResp = await request.patch(`${baseURL}/tasks/${taskId}/photos`, {
      data: {
        photos: [
          { step: 1, url: 'http://example.com/photo1.jpg' },
          { step: 2, url: 'http://example.com/photo2.jpg' },
          // ... up to 6
        ],
      },
    });
    expect(photosResp.ok()).toBeTruthy();

    // Step 4: Bot validates GPS (we'll update gps_validated field)
    const gpsResp = await request.patch(`${baseURL}/tasks/${taskId}/gps`, {
      data: { validated: true, latitude: 55.7558, longitude: 37.6176 },
    });
    expect(gpsResp.ok()).toBeTruthy();

    // Step 5: Bot submits meter readings
    const meterResp = await request.patch(`${baseURL}/tasks/${taskId}/meter`, {
      data: { reading: 12345 },
    });
    expect(meterResp.ok()).toBeTruthy();

    // Step 6: Bot submits cash amount
    const cashResp = await request.patch(`${baseURL}/tasks/${taskId}/cash`, {
      data: { amount: 1000 },
    });
    expect(cashResp.ok()).toBeTruthy();

    // Step 7: Bot uploads cash photo
    const cashPhotoResp = await request.patch(`${baseURL}/tasks/${taskId}/cash-photo`, {
      data: { url: 'http://example.com/cash.jpg' },
    });
    expect(cashPhotoResp.ok()).toBeTruthy();

    // Step 8: Bot adds comment
    const commentResp = await request.patch(`${baseURL}/tasks/${taskId}/comment`, {
      data: { comment: 'Test comment from bot' },
    });
    expect(commentResp.ok()).toBeTruthy();

    // Step 9: Bot marks task as completed
    const completeResp = await request.patch(`${baseURL}/tasks/${taskId}/complete`, {
      data: { completed_at: new Date().toISOString() },
    });
    expect(completeResp.ok()).toBeTruthy();

    // Step 10: Verify task is now in COMPLETED status
    const taskGetResp = await request.get(`${baseURL}/tasks/${taskId}`);
    expect(taskGetResp.ok()).toBeTruthy();
    const updatedTask = await taskGetResp.json();
    expect(updatedTask.status).toBe('COMPLETED');
  });

  test('bot simulates multiple tasks and checks statistics', async ({ request }) => {
    // Create several tasks
    for (let i = 0; i < 5; i++) {
      const taskResp = await request.post(`${baseURL}/tasks`, {
        data: {
          apparatus_id: apparatusId,
          technician_id: technicianId,
          type: 'TO',
          status: 'CREATED',
        },
      });
      expect(taskResp.ok()).toBeTruthy();
    }

    // Fetch tasks for the apparatus/technician and verify count
    const tasksResp = await request.get(`${baseURL}/tasks?apparatus_id=${apparatusId}&technician_id=${technicianId}`);
    expect(tasksResp.ok()).toBeTruthy();
    const tasks = await tasksResp.json();
    expect(tasks.length).toBeGreaterThanOrEqual(5);
  });

  test.afterAll(async ({ request }) => {
    // Clean up: delete the task, technician, apparatus (if API supports)
    // We'll skip cleanup for now, but in a real test we might want to clean up
  });
});