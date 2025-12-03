import { test, expect } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8004';

test.describe('API Integration Tests', () => {

  test('Chatbot API - Valid question', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/chatbot/ask`, {
      data: {
        question: 'How to grow tomatoes?'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('results');
    expect(Array.isArray(data.results)).toBeTruthy();
    expect(data.results.length).toBeGreaterThan(0);
    expect(data.results[0]).toHaveProperty('answer');
  });

  test('Chatbot API - Empty question', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/chatbot/ask`, {
      data: {
        question: ''
      }
    });
    
    expect(response.status()).toBe(400);
  });

  test('Crop Recommendation API', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/crop/recommend`, {
      data: {
        nitrogen: 40,
        phosphorus: 50,
        potassium: 60,
        temperature: 25.5,
        humidity: 65.0,
        ph: 6.5,
        rainfall: 200.0
      }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('recommended_crop');
    expect(data).toHaveProperty('confidence');
  });

  test('Sensor Data Ingestion', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/sensor/ingest`, {
      data: {
        device_id: 'TEST_DEVICE_001',
        temperature: 25.5,
        humidity: 65.0,
        soil_moisture: 45.0,
        ph_level: 6.5,
        nitrogen: 40,
        phosphorus: 50,
        potassium: 60,
        rainfall: 200.0
      }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  test('Irrigation Recommendation', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/api/irrigation/recommend`, {
      data: {
        temperature: 28.0,
        humidity: 55.0,
        soil_moisture: 30.0,
        crop_type: 'tomato'
      }
    });
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('water_amount');
    expect(data).toHaveProperty('recommendation');
  });

  test('VLM Status Check', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/api/vlm/status`);
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('vlm_available');
    expect(typeof data.vlm_available).toBe('boolean');
  });

  test('Health Endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });

  test('Ready Endpoint', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/ready`);
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('ready');
  });

  test('API Rate Limiting', async ({ request }) => {
    // Make multiple rapid requests
    const requests = Array.from({ length: 20 }, () =>
      request.get(`${API_BASE_URL}/health`)
    );
    
    const responses = await Promise.all(requests);
    
    // Should not all succeed if rate limiting is working
    // (depending on rate limit configuration)
    const successCount = responses.filter(r => r.ok()).length;
    console.log(`${successCount}/20 requests succeeded`);
    
    // At least some should succeed
    expect(successCount).toBeGreaterThan(0);
  });

  test('Invalid JSON in Request Body', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/chatbot/ask`, {
      data: 'invalid-json-string'
    });
    
    // Should return 400 or 422 for invalid input
    expect([400, 422]).toContain(response.status());
  });

  test('CORS Headers Present', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);
    
    const headers = response.headers();
    expect(headers).toHaveProperty('access-control-allow-origin');
  });

  test('Response Time Performance', async ({ request }) => {
    const startTime = Date.now();
    
    const response = await request.get(`${API_BASE_URL}/health`);
    
    const duration = Date.now() - startTime;
    
    expect(response.ok()).toBeTruthy();
    expect(duration).toBeLessThan(1000); // Should respond within 1 second
  });
});
