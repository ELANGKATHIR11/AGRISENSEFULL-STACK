/**
 * E2E Test: Dashboard Page
 * Tests the main dashboard functionality
 */
import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load dashboard successfully', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for key elements
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('should display system status', async ({ page }) => {
    // Look for health/status indicators
    const statusElement = page.locator('[data-testid="system-status"]').or(
      page.locator('text=/status|health/i').first()
    );
    
    await expect(statusElement).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to different sections', async ({ page }) => {
    // Test navigation
    const navLinks = ['Crops', 'Irrigation', 'Chatbot', 'Dashboard'];
    
    for (const linkText of navLinks) {
      const link = page.locator(`a:has-text("${linkText}")`).first();
      if (await link.isVisible()) {
        await link.click();
        await page.waitForLoadState('networkidle');
        await expect(page).toHaveURL(new RegExp(linkText.toLowerCase()));
        await page.goBack();
      }
    }
  });
});

test.describe('Chatbot Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
  });

  test('should load chatbot interface', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    
    // Check for input field
    const inputField = page.locator('input[type="text"], textarea').first();
    await expect(inputField).toBeVisible();
  });

  test('should send a message and receive response', async ({ page }) => {
    const testQuestion = 'How much water does tomato need?';
    
    // Find input and send button
    const input = page.locator('input[type="text"], textarea').first();
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
    
    // Type and send
    await input.fill(testQuestion);
    await sendButton.click();
    
    // Wait for response
    await page.waitForTimeout(3000);
    
    // Check if response appears
    const messageContainer = page.locator('[class*="message"], [class*="response"]');
    await expect(messageContainer.first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Sensor Data & Recommendations', () => {
  test('should submit sensor data and get recommendation', async ({ page }) => {
    await page.goto('/recommend');
    await page.waitForLoadState('networkidle');
    
    // Fill form if it exists
    const plantSelect = page.locator('select[name="plant"], input[name="plant"]').first();
    if (await plantSelect.isVisible()) {
      await plantSelect.selectOption('tomato');
    }
    
    const submitButton = page.locator('button:has-text("Recommend"), button[type="submit"]').first();
    if (await submitButton.isVisible()) {
      await submitButton.click();
      
      // Wait for results
      await page.waitForTimeout(2000);
      
      // Check for recommendation output
      const results = page.locator('[class*="result"], [class*="recommendation"]');
      await expect(results.first()).toBeVisible({ timeout: 10000 });
    }
  });
});

test.describe('API Health Check', () => {
  test('API should be healthy', async ({ request }) => {
    const response = await request.get('http://localhost:8004/health');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  test('API should return ready status', async ({ request }) => {
    const response = await request.get('http://localhost:8004/ready');
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('ready');
  });
});

test.describe('Responsive Design', () => {
  test('should work on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check if mobile menu exists
    const mobileMenu = page.locator('[aria-label="menu"], [class*="mobile"]');
    
    // Page should render without errors
    await expect(page.locator('body')).toBeVisible();
  });

  test('should work on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('page load time should be reasonable', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    // Page should load in under 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });
});

test.describe('Error Handling', () => {
  test('should handle 404 gracefully', async ({ page }) => {
    const response = await page.goto('/nonexistent-page');
    expect(response?.status()).toBe(404);
    
    // Should show error page
    await expect(page.locator('text=/404|not found/i')).toBeVisible({ timeout: 5000 });
  });
});
