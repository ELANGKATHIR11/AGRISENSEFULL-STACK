import { test, expect } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8004';

test.describe('AgriSense - Critical User Flows', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
    
    // Wait for app to load
    await page.waitForLoadState('networkidle');
  });

  test('Homepage loads successfully', async ({ page }) => {
    // Verify page title
    await expect(page).toHaveTitle(/AgriSense/i);
    
    // Check for main navigation
    await expect(page.locator('nav')).toBeVisible();
    
    // Verify key sections are present
    await expect(page.getByRole('heading', { name: /AgriSense/i })).toBeVisible();
  });

  test('Language switcher works', async ({ page }) => {
    // Find language selector
    const languageSelector = page.locator('[data-testid="language-selector"]');
    
    if (await languageSelector.isVisible()) {
      // Click language selector
      await languageSelector.click();
      
      // Select Hindi
      await page.getByText('हिंदी').click();
      
      // Verify content changed to Hindi
      await expect(page.locator('body')).toContainText(/कृषि/);
      
      // Switch back to English
      await languageSelector.click();
      await page.getByText('English').click();
      
      await expect(page.locator('body')).toContainText(/Agriculture/i);
    }
  });

  test('Navigation between pages works', async ({ page }) => {
    // Navigate to Dashboard
    await page.getByRole('link', { name: /Dashboard/i }).click();
    await expect(page).toHaveURL(/dashboard/);
    
    // Navigate to Crop Recommendation
    await page.getByRole('link', { name: /Crop/i }).click();
    await expect(page).toHaveURL(/crop/);
    
    // Navigate to Disease Detection
    await page.getByRole('link', { name: /Disease/i }).click();
    await expect(page).toHaveURL(/disease/);
  });

  test('Chatbot interaction works', async ({ page }) => {
    // Navigate to chatbot page
    await page.goto('/chatbot');
    
    // Find chat input
    const chatInput = page.locator('input[type="text"]').first();
    const sendButton = page.getByRole('button', { name: /Send|Submit/i });
    
    // Type a question
    await chatInput.fill('How to grow tomatoes?');
    
    // Send message
    await sendButton.click();
    
    // Wait for response
    await page.waitForSelector('[data-testid="chat-response"]', { timeout: 10000 });
    
    // Verify response is displayed
    const response = page.locator('[data-testid="chat-response"]').last();
    await expect(response).toBeVisible();
    await expect(response).not.toBeEmpty();
  });

  test('Sensor dashboard displays data', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Wait for data to load
    await page.waitForLoadState('networkidle');
    
    // Check for sensor readings
    const temperatureReading = page.locator('[data-testid="temperature"]');
    const humidityReading = page.locator('[data-testid="humidity"]');
    
    // Verify readings are displayed
    if (await temperatureReading.isVisible()) {
      await expect(temperatureReading).not.toBeEmpty();
    }
    
    if (await humidityReading.isVisible()) {
      await expect(humidityReading).not.toBeEmpty();
    }
  });

  test('Crop recommendation form submission', async ({ page }) => {
    // Navigate to crop recommendation page
    await page.goto('/crop-recommendation');
    
    // Fill in the form
    await page.locator('input[name="nitrogen"]').fill('40');
    await page.locator('input[name="phosphorus"]').fill('50');
    await page.locator('input[name="potassium"]').fill('60');
    await page.locator('input[name="temperature"]').fill('25');
    await page.locator('input[name="humidity"]').fill('65');
    await page.locator('input[name="ph"]').fill('6.5');
    await page.locator('input[name="rainfall"]').fill('200');
    
    // Submit form
    await page.getByRole('button', { name: /Recommend|Submit/i }).click();
    
    // Wait for results
    await page.waitForSelector('[data-testid="crop-result"]', { timeout: 10000 });
    
    // Verify recommendation is displayed
    const result = page.locator('[data-testid="crop-result"]');
    await expect(result).toBeVisible();
    await expect(result).toContainText(/crop|rice|wheat|maize/i);
  });

  test('Disease detection image upload (mock)', async ({ page }) => {
    // Navigate to disease detection page
    await page.goto('/disease-detection');
    
    // Check if file input exists
    const fileInput = page.locator('input[type="file"]');
    
    if (await fileInput.isVisible()) {
      // Note: In real tests, you would upload an actual test image
      // For now, verify the upload UI is present
      await expect(fileInput).toBeVisible();
      
      // Verify submit button is present
      const submitButton = page.getByRole('button', { name: /Detect|Analyze/i });
      await expect(submitButton).toBeVisible();
    }
  });

  test('Mobile responsive design', async ({ page, isMobile }) => {
    if (isMobile) {
      // Navigate to home
      await page.goto('/');
      
      // Check for mobile menu toggle
      const mobileMenuButton = page.locator('[data-testid="mobile-menu-toggle"]');
      
      if (await mobileMenuButton.isVisible()) {
        // Open mobile menu
        await mobileMenuButton.click();
        
        // Verify menu is visible
        const mobileMenu = page.locator('[data-testid="mobile-menu"]');
        await expect(mobileMenu).toBeVisible();
        
        // Close menu
        await mobileMenuButton.click();
        await expect(mobileMenu).toBeHidden();
      }
    }
  });

  test('Error handling for invalid inputs', async ({ page }) => {
    // Navigate to crop recommendation
    await page.goto('/crop-recommendation');
    
    // Submit empty form
    await page.getByRole('button', { name: /Recommend|Submit/i }).click();
    
    // Verify error messages appear
    const errorMessages = page.locator('.error-message, [role="alert"]');
    await expect(errorMessages.first()).toBeVisible();
  });

  test('Backend API health check', async ({ request }) => {
    // Test backend health endpoint
    const response = await request.get(`${API_BASE_URL}/health`);
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status');
    expect(data.status).toBe('healthy');
  });

  test('VLM status endpoint', async ({ request }) => {
    // Test VLM status endpoint
    const response = await request.get(`${API_BASE_URL}/api/vlm/status`);
    
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data).toHaveProperty('vlm_available');
  });
});
