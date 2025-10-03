/**
 * PWA UI Components for AgriSense
 * Install banner and offline indicator components
 */
import React, { useState } from 'react';
import { useOnlineStatus, usePWAInstall } from '../hooks/usePWA';

// PWA Install Banner Component
export function PWAInstallBanner() {
  const { isInstallable, promptInstall } = usePWAInstall();
  const [dismissed, setDismissed] = useState(() => 
    localStorage.getItem('agrisense-install-dismissed') === 'true'
  );

  if (!isInstallable || dismissed) return null;

  const handleInstall = async () => {
    const success = await promptInstall();
    if (!success) {
      setDismissed(true);
      localStorage.setItem('agrisense-install-dismissed', 'true');
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('agrisense-install-dismissed', 'true');
  };

  return (
    <div className="fixed bottom-4 left-4 right-4 bg-green-600 text-white p-4 rounded-lg shadow-lg z-50 md:left-auto md:right-4 md:max-w-sm">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="font-semibold">Install AgriSense</h3>
          <p className="text-sm opacity-90">Get the full app experience with offline access</p>
        </div>
        <div className="flex gap-2 ml-4">
          <button
            onClick={handleInstall}
            className="bg-white text-green-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100"
          >
            Install
          </button>
          <button
            onClick={handleDismiss}
            className="text-white/70 hover:text-white"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}

// Offline Indicator Component
export function OfflineIndicator() {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white px-4 py-2 text-center text-sm z-50">
      <span className="inline-block w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
      You're offline. Data will sync when connection is restored.
    </div>
  );
}

// Update Available Banner
export function UpdateAvailableBanner() {
  const [show, setShow] = useState(false);

  React.useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'SW_UPDATE_AVAILABLE') {
        setShow(true);
      }
    };

    navigator.serviceWorker?.addEventListener('message', handleMessage);
    return () => navigator.serviceWorker?.removeEventListener('message', handleMessage);
  }, []);

  const handleUpdate = () => {
    navigator.serviceWorker?.controller?.postMessage({ type: 'SKIP_WAITING' });
    window.location.reload();
  };

  if (!show) return null;

  return (
    <div className="fixed top-0 left-0 right-0 bg-blue-600 text-white px-4 py-2 text-center text-sm z-50">
      <div className="flex items-center justify-center gap-4">
        <span>A new version is available!</span>
        <button
          onClick={handleUpdate}
          className="bg-white text-blue-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100"
        >
          Update
        </button>
        <button
          onClick={() => setShow(false)}
          className="text-white/70 hover:text-white"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// PWA Status Component
export function PWAStatus() {
  const isOnline = useOnlineStatus();
  const { isInstalled } = usePWAInstall();

  return (
    <div className="flex items-center gap-2 text-xs text-gray-600">
      <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
      <span>{isOnline ? 'Online' : 'Offline'}</span>
      {isInstalled && (
        <>
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
          <span>Installed</span>
        </>
      )}
    </div>
  );
}