# 🧪 AgriSense - End-to-End Testing Guide

**Last Updated**: January 2025  
**Framework**: Playwright  
**Status**: Production Ready ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Running Tests](#running-tests)
4. [Test Structure](#test-structure)
5. [Writing New Tests](#writing-new-tests)
6. [CI/CD Integration](#cicd-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

AgriSense uses **Playwright** for end-to-end testing across multiple browsers and devices.

### Test Coverage

- ✅ **Critical User Flows**: Homepage, navigation, language switching
- ✅ **API Integration**: Backend endpoints, error handling, rate limiting
- ✅ **Form Submissions**: Crop recommendation, sensor data input
- ✅ **Chatbot Interaction**: Question-answer flow
- ✅ **Mobile Responsiveness**: Mobile viewports for iOS and Android
- ✅ **Performance**: Response time checks
- ✅ **Security**: CORS headers, input validation

### Browsers & Devices Tested

- **Desktop**: Chromium, Firefox, WebKit (Safari)
- **Mobile**: Chrome on Pixel 5, Safari on iPhone 12

---

## Installation

### Prerequisites

- Node.js 18+
- Docker & Docker Compose (for local test environment)

### Install Dependencies

```powershell
cd "AGRISENSE FULL-STACK\AGRISENSEFULL-STACK"

# Install Playwright and dependencies
npm install

# Install browser binaries
npx playwright install

# Install system dependencies (Linux only)
# npx playwright install-deps
```

---

## Running Tests

### 1. Start Test Environment

**Option A: Docker Compose (Recommended)**
```powershell
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
Start-Sleep -Seconds 30

# Verify services are running
curl http://localhost:80/health
curl http://localhost:8004/health
```

**Option B: Manual Start**
```powershell
# Terminal 1: Backend
cd AGRISENSEFULL-STACK
.\.venv\Scripts\Activate.ps1
python -m uvicorn agrisense_app.backend.main:app --port 8004

# Terminal 2: Frontend
cd agrisense_app\frontend\farm-fortune-frontend-main
npm run dev
```

### 2. Run E2E Tests

**All Tests (Headless)**
```powershell
npm test
```

**All Tests (Headed - See Browser)**
```powershell
npm run test:headed
```

**Interactive UI Mode**
```powershell
npm run test:ui
```

**Specific Browser**
```powershell
# Chromium only
npm run test:chromium

# Firefox only
npm run test:firefox

# WebKit only
npm run test:webkit

# Mobile devices
npm run test:mobile
```

**Debug Mode**
```powershell
npm run test:debug
```

**Specific Test File**
```powershell
npx playwright test e2e/critical-flows.spec.ts
```

**Specific Test Case**
```powershell
npx playwright test -g "Homepage loads successfully"
```

### 3. View Test Reports

```powershell
# Open HTML report
npm run report

# View in browser
Start-Process "playwright-report/index.html"
```

---

## Test Structure

### Directory Layout

```
AGRISENSEFULL-STACK/
├── e2e/
│   ├── critical-flows.spec.ts      # Main user flow tests
│   ├── api-integration.spec.ts     # Backend API tests
│   └── ...                          # Additional test files
├── playwright.config.ts             # Playwright configuration
├── package.json                     # E2E test dependencies
└── playwright-report/               # Test reports (generated)
```

### Configuration (`playwright.config.ts`)

```typescript
export default defineConfig({
  testDir: './e2e',
  
  use: {
    baseURL: 'http://localhost:80',       // Frontend URL
    apiURL: 'http://localhost:8004',      // Backend URL
    trace: 'on-first-retry',              // Debug traces
    screenshot: 'only-on-failure',        // Screenshots
    video: 'retain-on-failure',           // Videos
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },
  ],
});
```

---

## Writing New Tests

### Test Template

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to starting page
    await page.goto('/feature-page');
  });

  test('Test case description', async ({ page }) => {
    // 1. Arrange - Set up test data
    const input = page.locator('input[name="field"]');
    
    // 2. Act - Perform action
    await input.fill('test value');
    await page.getByRole('button', { name: /Submit/i }).click();
    
    // 3. Assert - Verify result
    await expect(page.locator('.result')).toBeVisible();
    await expect(page.locator('.result')).toContainText('Expected text');
  });
});
```

### Common Patterns

**1. Navigation**
```typescript
await page.goto('/dashboard');
await page.waitForLoadState('networkidle');
```

**2. Form Filling**
```typescript
await page.locator('input[name="nitrogen"]').fill('40');
await page.locator('input[name="phosphorus"]').fill('50');
await page.getByRole('button', { name: /Submit/i }).click();
```

**3. Waiting for Elements**
```typescript
// Wait for element to be visible
await page.waitForSelector('[data-testid="result"]');

// Wait for response
await page.waitForResponse(response => 
  response.url().includes('/api/crop') && response.status() === 200
);
```

**4. API Testing**
```typescript
const response = await request.post('http://localhost:8004/api/endpoint', {
  data: { key: 'value' }
});

expect(response.ok()).toBeTruthy();
const data = await response.json();
expect(data).toHaveProperty('expectedField');
```

**5. Mobile Testing**
```typescript
test('Mobile feature', async ({ page, isMobile }) => {
  if (isMobile) {
    // Mobile-specific test
    const mobileMenu = page.locator('[data-testid="mobile-menu"]');
    await expect(mobileMenu).toBeVisible();
  }
});
```

**6. Screenshot Comparison**
```typescript
await expect(page).toHaveScreenshot('feature-page.png');
```

**7. Network Interception**
```typescript
await page.route('**/api/endpoint', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ mocked: 'data' })
  });
});
```

### Best Practices

1. **Use `data-testid` attributes** for stable selectors:
   ```html
   <button data-testid="submit-button">Submit</button>
   ```
   ```typescript
   await page.locator('[data-testid="submit-button"]').click();
   ```

2. **Use semantic roles** when possible:
   ```typescript
   await page.getByRole('button', { name: /Submit/i }).click();
   await page.getByRole('heading', { name: /Dashboard/i });
   ```

3. **Group related tests** with `test.describe`:
   ```typescript
   test.describe('Crop Recommendation', () => {
     test('valid input', async ({ page }) => { ... });
     test('invalid input', async ({ page }) => { ... });
   });
   ```

4. **Use beforeEach for setup**:
   ```typescript
   test.beforeEach(async ({ page }) => {
     await page.goto('/feature');
     // Common setup
   });
   ```

5. **Add meaningful assertions**:
   ```typescript
   // ✅ Good
   await expect(result).toContainText('tomato');
   
   // ❌ Bad
   await expect(result).not.toBeEmpty();
   ```

---

## CI/CD Integration

### GitHub Actions Workflow

E2E tests are already integrated into `.github/workflows/ci.yml`:

```yaml
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        npm install
        npx playwright install --with-deps
    
    - name: Start services
      run: docker-compose -f docker-compose.dev.yml up -d
    
    - name: Wait for services
      run: |
        sleep 30
        curl -f http://localhost:80/health
        curl -f http://localhost:8004/health
    
    - name: Run E2E tests
      run: npm test
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: playwright-report
        path: playwright-report/
```

### Running in CI

**Environment Variables**:
```bash
export BASE_URL=http://localhost:80
export API_URL=http://localhost:8004
export CI=true
```

**Headless Mode** (default in CI):
- No GUI windows
- Faster execution
- Screenshots/videos only on failure

---

## Troubleshooting

### Common Issues

#### 1. **Tests Timeout**

```
Error: Test timeout of 30000ms exceeded
```

**Solutions**:
- Increase timeout: `test.setTimeout(60000)`
- Check if services are running: `curl http://localhost:80/health`
- Verify network connectivity

#### 2. **Element Not Found**

```
Error: Locator.click: Target closed
```

**Solutions**:
- Wait for element: `await page.waitForSelector('.element')`
- Use more specific selectors
- Check if element is in a different frame

#### 3. **Services Not Ready**

```
Error: connect ECONNREFUSED 127.0.0.1:8004
```

**Solutions**:
```powershell
# Restart services
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

# Wait longer
Start-Sleep -Seconds 60

# Check logs
docker-compose logs backend
docker-compose logs frontend
```

#### 4. **Browser Not Installed**

```
Error: Executable doesn't exist
```

**Solution**:
```powershell
npx playwright install
```

#### 5. **Port Conflict**

```
Error: Address already in use
```

**Solution**:
```powershell
# Windows
netstat -ano | findstr :8004
taskkill /PID <PID> /F

# Or use different ports in docker-compose.dev.yml
```

### Debug Tools

**1. Playwright Inspector**
```powershell
npm run test:debug
```

**2. Trace Viewer**
```powershell
npx playwright show-trace test-results/trace.zip
```

**3. Codegen (Record Tests)**
```powershell
npm run codegen
```

**4. Verbose Logging**
```powershell
$env:DEBUG="pw:api"
npm test
```

---

## Test Coverage

Run tests with coverage:

```powershell
# Run all tests
npm test

# View report
npm run report
```

**Current Coverage**:
- ✅ Critical user flows: 10 tests
- ✅ API integration: 12 tests
- ✅ Total: 22 end-to-end tests

---

## Additional Resources

- **Playwright Docs**: https://playwright.dev/
- **Best Practices**: https://playwright.dev/docs/best-practices
- **API Testing**: https://playwright.dev/docs/api-testing
- **CI/CD Guide**: https://playwright.dev/docs/ci

---

**Document Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintained By**: AgriSense QA Team  
**Status**: Production Ready ✅
