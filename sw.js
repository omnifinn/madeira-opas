// Madeira-opas service worker
// Cache-first strategy with network fallback for offline support
const CACHE = 'madeira-v4';
const PLACE_IDS = [
  'funchal-old','monte-palace','pico-arieiro','pico-ruivo','porto-moniz',
  'seixal','veu-da-noiva','fanal','25-fontes','santana','rocha-navio',
  'aguage','sao-vicente','boaventura','ponta-do-sol','cascata-anjos',
  'lombinho','risco','dolphins','doca-cavacas','praia-formosa','cabo-girao'
];
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  ...PLACE_IDS.map(id => `./images/${id}.webp`)
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  e.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req).then(resp => {
        // Cache map tiles, OSRM routes, and CDN assets on the fly
        if (resp && resp.status === 200 && (
            req.url.includes('tile.openstreetmap.org') ||
            req.url.includes('unpkg.com') ||
            req.url.includes('router.project-osrm.org')
        )) {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return resp;
      }).catch(() => {
        // Offline fallback for HTML navigation
        if (req.mode === 'navigate') return caches.match('./index.html');
        return new Response('Offline', { status: 503, statusText: 'Offline' });
      });
    })
  );
});
