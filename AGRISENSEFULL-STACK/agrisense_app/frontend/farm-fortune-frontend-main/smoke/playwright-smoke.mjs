import fs from 'fs/promises';
import path from 'path';
import { chromium } from 'playwright';

// Simple Playwright smoke test that:
// - launches headless Chromium
// - grants geolocation permission and sets coords
// - navigates to the Harvesting SPA route
// - captures network requests, console messages, and final HTML
// - writes outputs to ./smoke-output/

const OUT_DIR = path.resolve(process.cwd(), 'smoke-output');
const UI_ROOT = 'http://127.0.0.1:8004/ui';
const TARGET = UI_ROOT + '/harvesting';

async function run() {
  await fs.mkdir(OUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    permissions: ['geolocation'],
    geolocation: { latitude: 27.7172, longitude: 85.3240 }, // Kathmandu as a safe default
  });

  const page = await context.newPage();

  const network = [];
  page.on('request', (req) => {
    network.push({ type: 'request', url: req.url(), method: req.method(), headers: req.headers(), postData: req.postData() });
  });
  page.on('response', async (res) => {
    let size = null;
    try {
      const headers = res.headers();
      if (headers['content-length']) size = Number(headers['content-length']);
    } catch (e) {
      // ignore
    }
    network.push({ type: 'response', url: res.url(), status: res.status(), headers: res.headers(), size });
  });

  const consoles = [];
  page.on('console', (msg) => {
    consoles.push({ type: msg.type(), text: msg.text() });
  });

  // navigation
  console.log(`Navigating to ${UI_ROOT} (load SPA index) and then pushState to ${TARGET}`);
  try {
    // Load SPA index (this will return index.html)
    await page.goto(UI_ROOT, { waitUntil: 'networkidle', timeout: 30000 });
    // Ensure the app JS executes and mount happens
    await page.waitForTimeout(1000);
    // Navigate client-side to the harvesting route to avoid server-side 404 on deep link
    await page.evaluate((t) => {
      try {
        window.history.pushState({}, '', t);
        window.dispatchEvent(new PopStateEvent('popstate'));
      } catch (e) {
        // ignore
      }
    }, TARGET);
    // Wait for client navigation and fetches
    await page.waitForTimeout(3000);
  } catch (e) {
    console.error('Navigation failed:', e && e.message ? e.message : e);
  }

  const html = await page.content();

  // write outputs
  await fs.writeFile(path.join(OUT_DIR, 'harvesting.html'), html, 'utf8');
  await fs.writeFile(path.join(OUT_DIR, 'network.json'), JSON.stringify(network, null, 2), 'utf8');
  await fs.writeFile(path.join(OUT_DIR, 'console.json'), JSON.stringify(consoles, null, 2), 'utf8');

  console.log('Saved outputs to', OUT_DIR);

  await browser.close();
}

run().catch(async (err) => {
  console.error('Smoke test failed:', err);
  try { await fs.writeFile(path.join(OUT_DIR, 'error.txt'), String(err)); } catch {};
  process.exit(2);
});
