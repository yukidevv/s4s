const DB_NAME = "starts-sw";
const STORE = "kv";

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function saveUrl(url) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(url, "pageUrl");
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}

async function loadUrl() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get("pageUrl");
    req.onsuccess = () => resolve(req.result ?? null);
    req.onerror = () => reject(req.error);
  });
}

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SET_URL") {
    saveUrl(event.data.url);
  }
});

self.addEventListener("push", (event) => {
  let data = { title: "starts", body: "フィードを取得しました" };
  try {
    data = JSON.parse(event.data.text());
  } catch (e) {}

  event.waitUntil(
    self.registration.showNotification(data.title, { body: data.body })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then(async clients => {
      if (clients.length > 0) return clients[0].focus();
      const url = (await loadUrl()) ?? self.location.pathname.replace("/sw.js", "/");
      return self.clients.openWindow(url);
    })
  );
});
