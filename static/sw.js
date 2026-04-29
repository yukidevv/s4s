const CACHE = "starts-sw-v1";

async function saveUrl(url) {
  const cache = await caches.open(CACHE);
  await cache.put("pageUrl", new Response(url));
}

async function loadUrl() {
  const cache = await caches.open(CACHE);
  const res = await cache.match("pageUrl");
  return res ? res.text() : null;
}

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SET_URL") {
    event.waitUntil(saveUrl(event.data.url));
  }
});

self.addEventListener("push", (event) => {
  let data = { title: "starts", body: "フィードを取得しました" };
  try {
    data = JSON.parse(event.data.text());
  } catch (e) {}

  event.waitUntil(
    self.registration.showNotification(data.title, { body: data.body, icon: "/icon.svg" })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then(async clients => {
      if (clients.length > 0) return clients[0].focus();
      const url = (await loadUrl()) ?? self.registration.scope;
      return self.clients.openWindow(url);
    })
  );
});
