/*
 * 三国文字Roguelike - Service Worker
 * Minimal cache strategy:
 *   - Static assets (app.css, app.js, manifest, icons, index.html): cache-first with background revalidate
 *   - API calls (/api/*): network-only — game state MUST be live
 *
 * Why this is safe:
 *   - The game state lives in localStorage + server-side GameState.save/load.
 *   - Caching the JSON of /api/state would be a correctness bug (stale state).
 *   - Static files (CSS/JS/icons) are content-addressed by URL and safe to cache.
 *   - Versioned via CACHE_NAME; bumping the name forces a clean re-cache on update.
 */

const CACHE_NAME = 'sanguo-mvp-v6';
const STATIC_ASSETS = [
  './',
  './index.html',
  './app.css',
  './app.js',
  './manifest.webmanifest',
  './icons/icon.svg',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-167.png',
  './icons/icon-152.png'
];

// ── Install: pre-cache static assets ─────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Use {cache: 'reload'} to bypass any HTTP cache during install
      return Promise.allSettled(
        STATIC_ASSETS.map((url) =>
          cache.add(new Request(url, { cache: 'reload' })).catch(() => null)
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// ── Activate: clean old caches ───────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: network-first for /api/*, cache-first for static ─
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;  // never cache POST/PUT/DELETE

  const url = new URL(req.url);

  // Never cache API calls — game state must be live
  if (url.pathname.startsWith('/api/') || url.pathname === '/api') {
    event.respondWith(
      fetch(req).catch(() =>
        new Response(
          JSON.stringify({ error: 'offline', game_status: 'error' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // Cache-first for static assets, with network fallback
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        // Background revalidate (stale-while-revalidate pattern)
        fetch(req).then((res) => {
          if (res && res.status === 200 && res.type === 'basic') {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
        }).catch(() => {});
        return cached;
      }
      return fetch(req).then((res) => {
        // Only cache successful basic responses
        if (res && res.status === 200 && res.type === 'basic') {
          const clone = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
        }
        return res;
      }).catch(() => {
        // Offline fallback for navigation
        if (req.mode === 'navigate') {
          return caches.match('./index.html');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});
