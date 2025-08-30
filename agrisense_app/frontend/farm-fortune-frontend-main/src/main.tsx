import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

const root = createRoot(document.getElementById("root")!);
root.render(<App />);

// Register service worker (only in production and if supported)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
	window.addEventListener('load', () => {
		const swUrl = `${import.meta.env.BASE_URL}sw.js`;
		navigator.serviceWorker.register(swUrl).catch(() => {
			// ignore
		});
	});
}
