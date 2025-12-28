// Enhanced AgriSense Service Worker v2.0
// Advanced PWA features: offline mode, background sync, push notifications, caching strategies

const CACHE_NAME = 'agrisense-cache-v3';
const OFFLINE_CACHE = 'agrisense-offline-v3';
const DYNAMIC_CACHE = 'agrisense-dynamic-v3';
const IMAGES_CACHE = 'agrisense-images-v3';

const BASE = self.registration.scope.endsWith('/') ? self.registration.scope : self.registration.scope + '/';

// App Shell - Critical resources for offline functionality
const APP_SHELL = [
  BASE,
  BASE + 'index.html',
  BASE + 'logo-agrisense-mark-v2.svg',
  BASE + 'manifest.webmanifest',
  // Add critical CSS and JS here when using build output
];

// Offline fallback pages
const OFFLINE_PAGES = [
  BASE + 'offline.html'
];

// API endpoints that support offline functionality
const OFFLINE_APIS = [
  '/api/sensors/recent',
  '/api/weather/cache',
  '/api/tank/status',
  '/api/recommendations/recent'
];

// Background sync queues
const SYNC_QUEUES = {
  sensorData: 'sensor-data-sync',
  recommendations: 'recommendations-sync',
  alerts: 'alerts-sync'
};

// Cache strategies configuration
const CACHE_STRATEGIES = {
  documents: 'StaleWhileRevalidate',
  scripts: 'CacheFirst',
  styles: 'CacheFirst',
  images: 'CacheFirst',
  api: 'NetworkFirst',
  analytics: 'NetworkOnly'
};

// Install event - Cache app shell and offline resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing AgriSense Service Worker v3.0');
  
  event.waitUntil(
    (async () => {
      // Cache app shell
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(APP_SHELL);
      
      // Cache offline pages
      const offlineCache = await caches.open(OFFLINE_CACHE);
      await offlineCache.addAll(OFFLINE_PAGES);
      
      // Skip waiting to activate immediately
      self.skipWaiting();
      
      console.log('[SW] Installation complete');
    })()
  );
});

// Activate event - Clean old caches and claim clients
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating AgriSense Service Worker v3.0');
  
  event.waitUntil(
    (async () => {
      // Clean old caches
      const cacheNames = await caches.keys();
      const oldCaches = cacheNames.filter(name => 
        name !== CACHE_NAME && 
        name !== OFFLINE_CACHE && 
        name !== DYNAMIC_CACHE && 
        name !== IMAGES_CACHE
      );
      
      await Promise.all(oldCaches.map(name => caches.delete(name)));
      
      // Claim all clients
      await self.clients.claim();
      
      console.log('[SW] Activation complete');
    })()
  );
});

// Fetch event - Implement caching strategies
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests for caching
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different resource types
  if (url.origin === location.origin) {
    // Same-origin requests
    if (url.pathname.includes('/api/')) {
      event.respondWith(handleApiRequest(request));
    } else if (isImageRequest(request)) {
      event.respondWith(handleImageRequest(request));
    } else if (isDocumentRequest(request)) {
      event.respondWith(handleDocumentRequest(request));
    } else {
      event.respondWith(handleStaticResource(request));
    }
  } else {
    // Cross-origin requests (external APIs, CDNs)
    event.respondWith(handleExternalRequest(request));
  }
});

// API request handler - Network first with offline fallback
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('[SW] Network failed for API request:', url.pathname);
    
    // Check cache for offline support
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      // Add offline indicator header
      const offlineResponse = new Response(cachedResponse.body, {
        status: cachedResponse.status,
        statusText: cachedResponse.statusText,
        headers: {
          ...Object.fromEntries(cachedResponse.headers.entries()),
          'X-Served-By': 'ServiceWorker-Cache',
          'X-Cache-Date': new Date().toISOString()
        }
      });
      return offlineResponse;
    }
    
    // Return offline fallback for supported APIs
    if (OFFLINE_APIS.some(api => url.pathname.includes(api))) {
      return createOfflineFallback(url.pathname);
    }
    
    throw error;
  }
}

// Document request handler - Stale while revalidate
async function handleDocumentRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    // Return offline page if available
    return caches.match(BASE + 'offline.html');
  });
  
  return cachedResponse || fetchPromise;
}

// Image request handler - Cache first
async function handleImageRequest(request) {
  const cache = await caches.open(IMAGES_CACHE);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // Return placeholder image
    return new Response(createPlaceholderSVG(), {
      headers: { 'Content-Type': 'image/svg+xml' }
    });
  }
}

// Static resource handler - Cache first
async function handleStaticResource(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  const response = await fetch(request);
  if (response.ok) {
    cache.put(request, response.clone());
  }
  
  return response;
}

// External request handler - Network only with timeout
async function handleExternalRequest(request) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
  
  try {
    const response = await fetch(request, { signal: controller.signal });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// Helper functions
function isImageRequest(request) {
  return request.destination === 'image' || 
         request.url.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i);
}

function isDocumentRequest(request) {
  return request.destination === 'document';
}

function createOfflineFallback(pathname) {
  const fallbackData = {
    '/api/sensors/recent': {
      zone_id: 'offline',
      soil_moisture: 50,
      temperature: 25,
      humidity: 60,
      ph: 7.0,
      timestamp: new Date().toISOString(),
      offline: true
    },
    '/api/tank/status': {
      tank_id: 'offline',
      level_percent: 50,
      volume_liters: 1000,
      timestamp: new Date().toISOString(),
      offline: true
    }
  };
  
  const data = fallbackData[pathname] || { error: 'Offline mode', offline: true };
  
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'X-Served-By': 'ServiceWorker-Offline',
      'X-Cache-Date': new Date().toISOString()
    }
  });
}

function createPlaceholderSVG() {
  return `<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <rect width="200" height="200" fill="#f3f4f6"/>
    <text x="100" y="100" text-anchor="middle" dy=".3em" fill="#6b7280">
      Image Offline
    </text>
  </svg>`;
}

// Background Sync - Handle offline data submission
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === SYNC_QUEUES.sensorData) {
    event.waitUntil(syncSensorData());
  } else if (event.tag === SYNC_QUEUES.recommendations) {
    event.waitUntil(syncRecommendations());
  } else if (event.tag === SYNC_QUEUES.alerts) {
    event.waitUntil(syncAlerts());
  }
});

// Sync functions
async function syncSensorData() {
  try {
    const db = await openIndexedDB();
    const pendingData = await getStoredData(db, 'sensorData');
    
    for (const data of pendingData) {
      try {
        await fetch('/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data.payload)
        });
        
        await deleteStoredData(db, 'sensorData', data.id);
        console.log('[SW] Synced sensor data:', data.id);
      } catch (error) {
        console.error('[SW] Failed to sync sensor data:', data.id, error);
      }
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

async function syncRecommendations() {
  // Similar implementation for recommendations
  console.log('[SW] Syncing recommendations...');
}

async function syncAlerts() {
  // Similar implementation for alerts
  console.log('[SW] Syncing alerts...');
}

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: 'AgriSense notification',
    icon: BASE + 'icons/icon-128.png',
    badge: BASE + 'icons/icon-32.png',
    vibrate: [200, 100, 200],
    tag: 'agrisense-notification',
    requireInteraction: false,
    actions: [
      {
        action: 'view',
        title: 'View Details',
        icon: BASE + 'icons/icon-32.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: BASE + 'icons/icon-32.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      options.title = data.title || 'AgriSense Alert';
      options.body = data.body || data.message;
      options.data = data;
      options.tag = data.tag || 'agrisense-notification';
    } catch (error) {
      console.error('[SW] Failed to parse push data:', error);
      options.title = 'AgriSense';
      options.body = event.data.text();
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow(BASE + '?notification=' + event.notification.tag)
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then(windowClients => {
        // Focus existing window if available
        for (const client of windowClients) {
          if (client.url.includes(BASE) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Open new window
        return clients.openWindow(BASE);
      })
    );
  }
});

// IndexedDB helpers for offline storage
async function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AgriSenseOffline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      
      if (!db.objectStoreNames.contains('sensorData')) {
        const store = db.createObjectStore('sensorData', { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp');
      }
      
      if (!db.objectStoreNames.contains('recommendations')) {
        const store = db.createObjectStore('recommendations', { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp');
      }
      
      if (!db.objectStoreNames.contains('alerts')) {
        const store = db.createObjectStore('alerts', { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp');
      }
    };
  });
}

async function getStoredData(db, storeName) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

async function deleteStoredData(db, storeName, id) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(id);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

// Periodic cleanup
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CLEANUP_CACHES') {
    event.waitUntil(cleanupOldCaches());
  } else if (event.data && event.data.type === 'STORE_OFFLINE_DATA') {
    event.waitUntil(storeOfflineData(event.data.storeName, event.data.data));
  }
});

async function cleanupOldCaches() {
  const cacheNames = await caches.keys();
  const oldCaches = cacheNames.filter(name => !name.includes('v3'));
  await Promise.all(oldCaches.map(name => caches.delete(name)));
  console.log('[SW] Cleaned up old caches');
}

async function storeOfflineData(storeName, data) {
  try {
    const db = await openIndexedDB();
    const transaction = db.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    
    await new Promise((resolve, reject) => {
      const request = store.add({
        payload: data,
        timestamp: new Date().toISOString()
      });
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
    
    console.log('[SW] Stored offline data:', storeName);
  } catch (error) {
    console.error('[SW] Failed to store offline data:', error);
  }
}

console.log('[SW] AgriSense Service Worker v3.0 loaded');