import { chromium } from 'playwright';
import fs from 'fs/promises';
import path from 'path';

const OUT = path.resolve(process.cwd(), 'smoke-output', 'diagnose.json');
const UI_ROOT = 'http://127.0.0.1:8004/ui';
const TARGET = UI_ROOT + '/harvesting';

async function run() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ permissions: ['geolocation'], geolocation: { latitude: 27.7172, longitude: 85.3240 } });
  const page = await context.newPage();
  await page.goto(UI_ROOT, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(1000);
  await page.evaluate((t) => { window.history.pushState({}, '', t); window.dispatchEvent(new PopStateEvent('popstate')); }, TARGET);
  await page.waitForTimeout(1500);

  const diag = await page.evaluate(() => {
    const leaflets = Array.from(document.querySelectorAll('.leaflet-container')).map((el) => {
      const rect = el.getBoundingClientRect();
      return { width: rect.width, height: rect.height, classes: el.className };
    });
    const tiles = Array.from(document.querySelectorAll('img.leaflet-tile')).slice(0, 20).map((img) => ({ src: img.src, width: img.naturalWidth, height: img.naturalHeight }));
    const markers = Array.from(document.querySelectorAll('img.leaflet-marker-icon, img.leaflet-marker-shadow')).map((img) => ({ src: img.src, width: img.naturalWidth, height: img.naturalHeight, visible: !!img.offsetParent }));
    const rootEl = document.getElementById('root');
    const root = rootEl ? rootEl.getBoundingClientRect() : null;
    const localLat = localStorage.getItem('lat');
    const localLon = localStorage.getItem('lon');
    const geoLive = localStorage.getItem('geo_live');
    // Check for any visible popup text
    const popup = document.querySelector('.leaflet-popup-content')?.textContent?.slice?.(0, 200) || null;
    return { leaflets, tilesCount: document.querySelectorAll('img.leaflet-tile').length, tiles, markers, root: root ? { width: root.width, height: root.height } : null, localLat, localLon, geoLive, popup };
  });

  await fs.mkdir(path.dirname(OUT), { recursive: true });
  await fs.writeFile(OUT, JSON.stringify(diag, null, 2), 'utf8');
  console.log('Wrote diagnostics to', OUT);
  await browser.close();
}

run().catch((e) => { console.error(e); process.exit(2); });
