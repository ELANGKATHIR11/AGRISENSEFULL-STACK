import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { i18nPromise } from './i18n' // Initialize i18n before rendering

// Wait for i18n to be ready before rendering
i18nPromise.then(() => {
  const root = createRoot(document.getElementById("root")!);
  root.render(
    <StrictMode>
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
        <App />
      </Suspense>
    </StrictMode>
  );
}).catch((error) => {
  console.error('Failed to initialize i18n:', error);
  // Render app anyway with fallback language
  const root = createRoot(document.getElementById("root")!);
  root.render(
    <StrictMode>
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
        <App />
      </Suspense>
    </StrictMode>
  );
});

// Service worker temporarily disabled to fix caching issues
// if ('serviceWorker' in navigator && import.meta.env.PROD) {
// 	window.addEventListener('load', () => {
// 		const swUrl = `${import.meta.env.BASE_URL}sw.js`;
// 		navigator.serviceWorker.register(swUrl).catch(() => {
// 			// ignore
// 		});
// 	});
// }
