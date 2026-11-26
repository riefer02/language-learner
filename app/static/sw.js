// Kiku service worker: app shell caching + push reminders.
const CACHE_NAME = "kiku-shell-v4";
const SHELL = [
  "/offline",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/manifest.webmanifest",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
        )
      )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") {
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match(request).then((cached) => cached || caches.match("/offline"))
      )
    );
    return;
  }

  const url = new URL(request.url);
  // Only cache same-origin static files, by their exact URL. Versioned assets
  // are immutable; ignoring the query string would serve last release's CSS/JS.
  // Audio is served with Range requests (206) and can be large, so it stays out
  // of Cache Storage and is handled by the browser's media cache instead.
  if (
    url.origin !== self.location.origin ||
    !url.pathname.startsWith("/static/") ||
    url.pathname.startsWith("/static/audio/")
  ) {
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(request);
      if (cached) {
        return cached;
      }
      const response = await fetch(request);
      if (response.ok && response.status === 200) {
        const copy = response.clone();
        try {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(request, copy);
        } catch (_error) {
          // A cache failure must not break the asset response.
        }
      }
      return response;
    })()
  );
});

self.addEventListener("push", (event) => {
  let payload = {
    title: "Kiku",
    body: "A short Korean session is ready.",
    url: "/",
  };
  if (event.data) {
    try {
      payload = { ...payload, ...event.data.json() };
    } catch (_error) {
      payload.body = event.data.text();
    }
  }
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/favicon-32.png",
      tag: "kiku-daily",
      data: { url: payload.url },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(url) && "focus" in client) {
          return client.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "test") {
    self.registration.showNotification("Kiku", {
      body: "Notifications are working. One gentle reminder a day, max.",
      icon: "/static/icons/icon-192.png",
      tag: "kiku-test",
      data: { url: "/" },
    });
  }
});
