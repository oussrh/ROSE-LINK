/**
 * ROSE Link - Service Worker
 * Provides offline capability and caching for the PWA
 */

const CACHE_NAME = 'rose-link-v1';
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/css/custom.css',
    '/js/main.js',
    '/js/config.js',
    '/js/i18n.js',
    '/js/chartTheme.js',
    '/js/utils/dom.js',
    '/js/utils/toast.js',
    '/js/utils/api.js',
    '/js/components/vpn.js',
    '/js/components/wifi.js',
    '/js/components/system.js',
    '/js/components/hotspot.js',
    '/js/components/statusCards.js',
    '/js/components/tabs.js',
    '/vendor/htmx.min.js',
    '/vendor/lucide.min.js',
    '/locales/en.json',
    '/locales/fr.json',
    '/Logo.webp',
    '/Logo-250X178.webp',
    '/icon.webp',
    '/icon.png',
    '/favicon.ico',
    '/favicon.svg',
    '/favicon-16x16.png',
    '/favicon-32x32.png',
    '/apple-touch-icon.png',
    '/android-chrome-192x192.png',
    '/android-chrome-512x512.png',
    '/site.webmanifest',
    '/404.html'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // API requests - network first, no cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    return new Response(
                        JSON.stringify({ error: 'Offline', message: 'Network unavailable' }),
                        {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );
                })
        );
        return;
    }

    // Static assets - cache first, fallback to network
    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(request)
                    .then((networkResponse) => {
                        // Cache successful responses
                        if (networkResponse && networkResponse.status === 200) {
                            const responseClone = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then((cache) => cache.put(request, responseClone));
                        }
                        return networkResponse;
                    })
                    .catch(() => {
                        // Return offline page for navigation requests
                        if (request.mode === 'navigate') {
                            return caches.match('/404.html');
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Handle messages from main thread
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});
