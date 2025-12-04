const CACHE_NAME = "emcali-cache-v1";
const urlsToCache = [
  "/",
  "/static/icons/logo-pwa.png",
  "/static/icons/logo-pwa1.png"
];

// Instalar
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

// Activar
self.addEventListener("activate", event => {
  clients.claim();
});

// Interceptar requests
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    })
  );
});
