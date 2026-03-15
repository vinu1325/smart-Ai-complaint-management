const CACHE_NAME = 'vinu-smart-ai-v1';
const assets = [
  '/',
  '/index.html',
  '/styles.css',
  '/js/app.js',
  '/img/logo.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(assets);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((res) => {
      return res || fetch(e.request);
    })
  );
});
