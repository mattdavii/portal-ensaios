const CACHE_VERSION = 'portal-v2-20260821';
const CORE = ['/', '/style.css', '/ui.js', '/rascunho.js', '/resistencia.js', '/manifest.json', '/logo.png', '/trafo', '/tp', '/tc', '/disjuntor-mt', '/disjuntor-bt', '/seccionadora', '/res-malha', '/cont-malha', '/cabos-cc', '/conversor-resistencia'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_VERSION).then(cache => cache.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    event.respondWith(caches.match(req).then(cached => {
      const rede = fetch(req).then(res => {
        if (res && res.ok) caches.open(CACHE_VERSION).then(cache => cache.put(req, res.clone()));
        return res;
      }).catch(() => cached);
      return cached || rede;
    }));
  } else {
    event.respondWith(fetch(req).then(res => {
      if (res && res.ok) caches.open(CACHE_VERSION).then(cache => cache.put(req, res.clone()));
      return res;
    }).catch(() => caches.match(req)));
  }
});
