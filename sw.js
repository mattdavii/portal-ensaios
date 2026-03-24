const CACHE_NAME = 'portal-v22';

// LISTA DE TUDO O QUE DEVE FUNCIONAR OFFLINE
const ASSETS = [
  '/',
  '/manifest.json',
  '/logo.png',
  '/cabos-cc',
  '/res-malha',
  '/cont-malha',
  '/disjuntor-mt',
  '/disjuntor-bt',
  '/seccionadora',
  '/trafo',
  '/tp',
  '/tc',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'
];

// Instalação e Cache inicial
self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
});

// Ativação e limpeza de cofres antigos
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
  )));
});

// OBRIGATÓRIO PARA OFFLINE: Se não tiver internet, puxa do cofre
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
