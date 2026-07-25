// HDWork service worker — cho cài PWA + chạy offline. An toàn: chỉ chạy khi mở qua http(s).
const CACHE = "hdwork-v2";
const CORE = ["./index.html", "./manifest.json", "./icon.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE).catch(() => {})).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  // Trang chính: ưu tiên mạng (luôn mới), offline thì lấy bản đã lưu.
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req)
        .then((r) => { const cp = r.clone(); caches.open(CACHE).then((c) => c.put("./index.html", cp)); return r; })
        .catch(() => caches.match("./index.html"))
    );
    return;
  }
  // Tài nguyên khác (thư viện CDN, icon…): ưu tiên cache, không có thì tải mạng rồi lưu.
  e.respondWith(
    caches.match(req).then((hit) =>
      hit || fetch(req).then((r) => {
        try { if (r && r.status === 200 && (r.type === "basic" || r.type === "cors")) { const cp = r.clone(); caches.open(CACHE).then((c) => c.put(req, cp)); } } catch (x) {}
        return r;
      }).catch(() => hit)
    )
  );
});
