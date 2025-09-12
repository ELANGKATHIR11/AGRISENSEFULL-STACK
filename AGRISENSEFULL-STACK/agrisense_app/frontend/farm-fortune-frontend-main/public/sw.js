// Simple service worker for offline shell and caching latest weather
const CACHE_NAME = 'agrisense-cache-v2';
const BASE = self.registration.scope.endsWith('/') ? self.registration.scope : self.registration.scope + '/';
const APP_SHELL = [
  BASE,
  BASE + 'index.html',
  BASE + 'logo-agrisense-mark-v2.svg',
  BASE + 'manifest.webmanifest',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Cache-first for app shell
  if (url.origin === location.origin) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
    return;
  }
  // Network-first for API with fallback to cache
  if (url.pathname.includes('/api/')) {
    event.respondWith((async () => {
      try {
        const res = await fetch(event.request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(event.request, res.clone());
        return res;
      } catch {
        const cached = await caches.match(event.request);
        if (cached) return cached;
        throw new Error('Network error and no cache');
      }
    })());
  }
});
