const CACHE_NAME = "fds-pos-cache-v1";
const OFFLINE_URL = "/offline";

self.addEventListener("install", (event) => {
  console.log("[ServiceWorker] Install");

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll([
        "/",
        "/protocol",
        "/static/style.css",
        "/static/icons/icon-192.png",
        "/static/icons/icon-512.png",
        "/static/manifest.json",
        OFFLINE_URL
      ])
    )
  );
  self.skipWaiting();  // Activate immediately
});

self.addEventListener("activate", (event) => {
  console.log("[ServiceWorker] Activated");
  // Clean up old caches if needed in future versions
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    fetch(event.request).catch(() =>
      caches.match(event.request).then((response) =>
        response || caches.match(OFFLINE_URL)
      )
    )
  );
});

