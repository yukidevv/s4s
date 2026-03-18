let pageUrl = null;

self.addEventListener("message", (event) => {
  if (event.data?.type === "SET_URL") {
    pageUrl = event.data.url;
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
    self.clients.matchAll({ type: "window" }).then(clients => {
      if (clients.length > 0) return clients[0].focus();
      const url = pageUrl ?? self.location.pathname.replace("/sw.js", "/");
      return self.clients.openWindow(url);
    })
  );
});
