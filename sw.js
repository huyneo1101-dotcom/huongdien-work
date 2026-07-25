/* Hương Diện service worker — app shell offline + network-first cho trang chính */
const CACHE = 'huongdien-v2';
const CORE = ['./', './index.html', './manifest.json', './icon.svg'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).catch(() => {}));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Trang chính: ưu tiên mạng để luôn nhận bản mới, offline thì lấy cache.
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((r) => { const cp = r.clone(); caches.open(CACHE).then((c) => c.put('./index.html', cp)); return r; })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Không cache Supabase (dữ liệu động).
  if (url.host.includes('supabase')) return;

  // Tài nguyên khác (CDN font/icon + jsdelivr): cache-first + lưu runtime để dùng offline.
  const ALLOW = ['jsdelivr', 'fonts.googleapis.com', 'fonts.gstatic.com'];
  e.respondWith(
    caches.match(req).then((cached) =>
      cached || fetch(req).then((r) => {
        if (r && r.ok && (url.origin === location.origin || ALLOW.some((h) => url.host.includes(h)))) {
          const cp = r.clone();
          caches.open(CACHE).then((c) => c.put(req, cp));
        }
        return r;
      }).catch(() => cached)
    )
  );
});
