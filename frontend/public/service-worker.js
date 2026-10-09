// Stratégie « réseau d'abord » : le cache ne sert qu'en secours hors-ligne, jamais à la place d'une version plus récente.
const CACHE_NAME = 'kaho-v2';
const PRECACHE = ['/', '/offline'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE).catch(() => undefined)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  // Jamais d'interception : autres origines (API, CDN), méthodes non-GET, rechargement à chaud du dev server
  if (request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/_next/webpack-hmr') || url.pathname.startsWith('/api/')) {
    return;
  }
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      })
      .catch(async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        if (request.mode === 'navigate') return caches.match('/offline');
        return Response.error();
      })
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
