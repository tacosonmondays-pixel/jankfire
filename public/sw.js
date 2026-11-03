// Minimal service worker so the game can be installed as an app.
// It never caches: the game always loads the latest version from the server.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
