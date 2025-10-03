/**
 * PWA utilities and hooks for AgriSense
 * Provides offline detection, background sync, push notifications, and installation prompt
 */
import { useState, useEffect, useCallback } from 'react';

// Types
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface SyncData {
  type: 'sensorData' | 'recommendations' | 'alerts';
  data: Record<string, unknown>;
  timestamp: string;
}

interface PWACapabilities {
  isInstallable: boolean;
  isInstalled: boolean;
  hasServiceWorker: boolean;
  supportsNotifications: boolean;
  supportsPush: boolean;
  supportsBackgroundSync: boolean;
}

// Hook for online/offline status
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// Hook for PWA installation
export function usePWAInstall() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if already installed
    const isInStandaloneMode = window.matchMedia('(display-mode: standalone)').matches;
    const isInWebAppMode = (window.navigator as { standalone?: boolean }).standalone === true;
    setIsInstalled(isInStandaloneMode || isInWebAppMode);

    // Listen for install prompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const promptEvent = e as BeforeInstallPromptEvent;
      setInstallPrompt(promptEvent);
      setIsInstallable(true);
    };

    // Listen for successful installation
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setInstallPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const promptInstall = useCallback(async () => {
    if (!installPrompt) return false;

    try {
      await installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      
      if (choice.outcome === 'accepted') {
        setIsInstallable(false);
        setInstallPrompt(null);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Install prompt failed:', error);
      return false;
    }
  }, [installPrompt]);

  return {
    isInstallable,
    isInstalled,
    promptInstall
  };
}

// Hook for service worker management
export function useServiceWorker() {
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null);
  const [isSupported, setIsSupported] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      setIsSupported(true);

      // Use Vite's BASE_URL so the service worker registers at the correct scope.
      // In production BASE_URL should be '/ui/' so the SW will be available at '/ui/sw-v2.js'
      // and scoped to '/ui/'. In dev it will be '/'.
      // import.meta.env is available at build time; fallback to '/' if missing.
      const base = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.BASE_URL) ? import.meta.env.BASE_URL : '/';
      const swUrl = `${base}sw-v2.js`;

      navigator.serviceWorker.register(swUrl)
        .then((reg) => {
          setRegistration(reg);

          // Check for updates
          reg.addEventListener('updatefound', () => {
            const newWorker = reg.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  setUpdateAvailable(true);
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error);
        });

      // Listen for messages from service worker
      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data?.type === 'CACHE_UPDATED') {
          // Handle cache updates
          console.log('Cache updated:', event.data);
        }
      });
    }
  }, []);

  const updateServiceWorker = useCallback(() => {
    if (registration && registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }, [registration]);

  const sendMessageToSW = useCallback((message: Record<string, unknown>) => {
    if (registration && registration.active) {
      registration.active.postMessage(message);
    }
  }, [registration]);

  return {
    isSupported,
    registration,
    updateAvailable,
    updateServiceWorker,
    sendMessageToSW
  };
}

// Hook for push notifications
export function usePushNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if ('Notification' in window && 'serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
      setPermission(Notification.permission);

      // Get existing subscription
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager.getSubscription().then((sub) => {
          setSubscription(sub);
        });
      });
    }
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!isSupported) return false;

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result === 'granted';
    } catch (error) {
      console.error('Notification permission request failed:', error);
      return false;
    }
  }, [isSupported]);

  const subscribe = useCallback(async (vapidPublicKey: string): Promise<PushSubscription | null> => {
    if (!isSupported || permission !== 'granted') return null;

    try {
      const registration = await navigator.serviceWorker.ready;
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidPublicKey
      });

      setSubscription(sub);
      
      // Send subscription to server
      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sub)
      });

      return sub;
    } catch (error) {
      console.error('Push subscription failed:', error);
      return null;
    }
  }, [isSupported, permission]);

  const unsubscribe = useCallback(async (): Promise<boolean> => {
    if (!subscription) return false;

    try {
      await subscription.unsubscribe();
      setSubscription(null);

      // Notify server
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ endpoint: subscription.endpoint })
      });

      return true;
    } catch (error) {
      console.error('Push unsubscription failed:', error);
      return false;
    }
  }, [subscription]);

  const showNotification = useCallback(async (title: string, options?: NotificationOptions) => {
    if (permission !== 'granted') return;

    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.showNotification(title, {
        icon: '/icons/icon-128.png',
        badge: '/icons/icon-32.png',
        ...options
      });
    } catch (error) {
      console.error('Show notification failed:', error);
    }
  }, [permission]);

  return {
    isSupported,
    permission,
    subscription,
    requestPermission,
    subscribe,
    unsubscribe,
    showNotification
  };
}

// Hook for background sync
export function useBackgroundSync() {
  const [isSupported, setIsSupported] = useState(false);
  const { sendMessageToSW } = useServiceWorker();

  useEffect(() => {
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      setIsSupported(true);
    }
  }, []);

  const scheduleSync = useCallback(async (tag: string): Promise<boolean> => {
    if (!isSupported) return false;

    try {
      const registration = await navigator.serviceWorker.ready;
      // Note: Background Sync API might not be available in all browsers
      if ('sync' in registration) {
        const syncRegistration = registration as ServiceWorkerRegistration & { sync: { register(tag: string): Promise<void> } };
        await syncRegistration.sync.register(tag);
      }
      return true;
    } catch (error) {
      console.error('Background sync registration failed:', error);
      return false;
    }
  }, [isSupported]);

  const storeForSync = useCallback(async (data: SyncData): Promise<boolean> => {
    try {
      // Store data for background sync
      sendMessageToSW({
        type: 'STORE_OFFLINE_DATA',
        storeName: data.type,
        data: data.data
      });

      // Schedule sync
      await scheduleSync(`${data.type}-sync`);
      return true;
    } catch (error) {
      console.error('Store for sync failed:', error);
      return false;
    }
  }, [sendMessageToSW, scheduleSync]);

  return {
    isSupported,
    scheduleSync,
    storeForSync
  };
}

// Hook for PWA capabilities detection
export function usePWACapabilities(): PWACapabilities {
  const [capabilities, setCapabilities] = useState<PWACapabilities>({
    isInstallable: false,
    isInstalled: false,
    hasServiceWorker: false,
    supportsNotifications: false,
    supportsPush: false,
    supportsBackgroundSync: false
  });

  const { isInstallable, isInstalled } = usePWAInstall();
  const { isSupported: swSupported } = useServiceWorker();
  const { isSupported: notifSupported } = usePushNotifications();

  useEffect(() => {
    setCapabilities({
      isInstallable,
      isInstalled,
      hasServiceWorker: swSupported,
      supportsNotifications: notifSupported,
      supportsPush: 'PushManager' in window,
      supportsBackgroundSync: 'sync' in window.ServiceWorkerRegistration.prototype
    });
  }, [isInstallable, isInstalled, swSupported, notifSupported]);

  return capabilities;
}

// Hook for offline data management
export function useOfflineData() {
  const isOnline = useOnlineStatus();
  const { storeForSync } = useBackgroundSync();

  const storeData = useCallback((key: string, data: Record<string, unknown>) => {
    try {
      localStorage.setItem(`agrisense-${key}`, JSON.stringify({
        data,
        timestamp: new Date().toISOString(),
        synced: isOnline
      }));
    } catch (error) {
      console.error('Failed to store offline data:', error);
    }
  }, [isOnline]);

  const getData = useCallback((key: string) => {
    try {
      const stored = localStorage.getItem(`agrisense-${key}`);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to retrieve offline data:', error);
      return null;
    }
  }, []);

  const submitData = useCallback(async (endpoint: string, data: Record<string, unknown>, syncType: SyncData['type']) => {
    if (isOnline) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        if (response.ok) {
          return { success: true, online: true };
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error) {
        console.error('Online submission failed:', error);
      }
    }

    // Store for background sync
    await storeForSync({
      type: syncType,
      data: { endpoint, payload: data },
      timestamp: new Date().toISOString()
    });

    return { success: true, online: false };
  }, [isOnline, storeForSync]);

  return {
    isOnline,
    storeData,
    getData,
    submitData
  };
}

// Utility functions
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  
  return outputArray;
}