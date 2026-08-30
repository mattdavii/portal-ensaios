const CACHE_VERSION = 'portal-v2-5-10-20260830';

const CORE = [
  '/',
  '/style.css',
  '/ui.js',
  '/rascunho.js',
  '/resistencia.js',
  '/manifest.json',
  '/logo.png',
  '/trafo',
  '/tp',
  '/tc',
  '/disjuntor-mt',
  '/disjuntor-bt',
  '/seccionadora',
  '/res-malha',
  '/cont-malha',
  '/cabos-cc',
  '/conversor-resistencia',
  '/queda-tensao',
  '/relacao-tc-tp',
  '/voc-string',
  '/desequilibrio-fases',
  '/riso-cabos-ca-mt',
  '/comparador-strings',
  '/riso-strings'
];

// Instala a nova versão e a mantém aguardando.
// Ela só assume o controle quando o usuário tocar em "Atualizar agora".
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then(cache => cache.addAll(CORE))
  );
});

// Quando a nova versão for ativada, remove caches antigos.
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(key => key !== CACHE_VERSION)
          .map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// Recebe o comando enviado pelo botão "Atualizar agora".
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', event => {
  const req = event.request;

  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Nunca deixa o próprio sw.js preso no cache.
  if (url.origin === self.location.origin && url.pathname === '/sw.js') {
    event.respondWith(
      fetch(req, { cache: 'no-store' })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Navegação: tenta a rede primeiro para reduzir o risco de abrir HTML antigo.
  if (req.mode === 'navigate' && url.origin === self.location.origin) {
    event.respondWith(
      fetch(req)
        .then(res => {
          if (res && res.ok) {
            const copia = res.clone();
            caches.open(CACHE_VERSION)
              .then(cache => cache.put(req, copia));
          }
          return res;
        })
        .catch(() =>
          caches.match(req)
            .then(cached => cached || caches.match('/'))
        )
    );
    return;
  }

  // Arquivos internos: cache primeiro + atualização em segundo plano.
  if (url.origin === self.location.origin) {
    event.respondWith(
      caches.match(req).then(cached => {
        const rede = fetch(req)
          .then(res => {
            if (res && res.ok) {
              caches.open(CACHE_VERSION)
                .then(cache => cache.put(req, res.clone()));
            }
            return res;
          })
          .catch(() => cached);

        return cached || rede;
      })
    );
    return;
  }

  // Recursos externos: rede primeiro, cache como fallback.
  event.respondWith(
    fetch(req)
      .then(res => {
        if (res && res.ok) {
          caches.open(CACHE_VERSION)
            .then(cache => cache.put(req, res.clone()));
        }
        return res;
      })
      .catch(() => caches.match(req))
  );
});
