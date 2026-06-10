// Service Worker para PWA - Catálogo de Mamíferos Extintos
// Versão 49.0.0

const CACHE_NAME = 'extinct-mammals-v54';
const RUNTIME_CACHE = 'extinct-mammals-runtime-v54';

// Recursos essenciais para cache inicial
const PRECACHE_URLS = [
  '/',
  '/static/css/style.css?v=1.0.4',
  '/static/css/alerts.css',
  '/static/css/cookie-consent.css',
  '/static/css/buttons_fix.css',
  '/static/css/error-pages.css',
  '/static/js/script.js',
  '/static/js/cookie-consent.js',
  '/static/manifest.json',
  '/offline/',
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {

        return cache.addAll(PRECACHE_URLS.map(url => new Request(url, {
          cache: 'reload'
        })));
      })
      .then(() => {

        return self.skipWaiting(); // Ativar imediatamente
      })
      .catch((error) => {
        console.error('[SW] Installation failed:', error);
      })
  );
});

// Ativação do Service Worker
self.addEventListener('activate', (event) => {

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        // Remover caches antigos
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith('extinct-mammals-') && 
                     cacheName !== CACHE_NAME && 
                     cacheName !== RUNTIME_CACHE;
            })
            .map((cacheName) => {

              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {

        return self.clients.claim(); // Assumir controle imediatamente
      })
  );
});

// Estratégia de cache: Network First com fallback para Cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignorar requisições não-GET
  if (request.method !== 'GET') {
    return;
  }
  
  // Ignorar requisições de admin e autenticação
  if (url.pathname.startsWith('/admin/') || 
      url.pathname.startsWith('/accounts/login/') ||
      url.pathname.startsWith('/accounts/logout/') ||
      url.pathname.startsWith('/accounts/register/')) {
    return;
  }
  
  // Estratégia para diferentes tipos de recursos
  if (url.pathname.startsWith('/static/')) {
    // Cache First para arquivos estáticos
    event.respondWith(cacheFirst(request));
  } else if (url.pathname.startsWith('/media/')) {
    // Cache First para imagens
    event.respondWith(cacheFirst(request));
  } else if (url.pathname.match(/\.(jpg|jpeg|png|gif|svg|webp|ico)$/)) {
    // Cache First para imagens
    event.respondWith(cacheFirst(request));
  } else {
    // Network First para páginas HTML e API
    event.respondWith(networkFirst(request));
  }
});

// Estratégia Cache First
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  
  if (cached) {

    return cached;
  }
  
  try {
    const response = await fetch(request);
    
    // Cache apenas respostas bem-sucedidas
    if (response.status === 200) {
      const responseClone = response.clone();
      cache.put(request, responseClone);

    }
    
    return response;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    
    // Retornar página offline se disponível
    const offlinePage = await cache.match('/offline/');
    if (offlinePage) {
      return offlinePage;
    }
    
    // Fallback genérico
    return new Response('Offline - Recurso não disponível', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Estratégia Network First
async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  
  try {
    const response = await fetch(request);
    
    // Cache apenas respostas bem-sucedidas
    if (response.status === 200) {
      const responseClone = response.clone();
      cache.put(request, responseClone);

    }
    
    return response;
  } catch (error) {
    console.error('[SW] Network request failed:', error);
    
    // Tentar buscar do cache
    const cached = await cache.match(request);
    if (cached) {

      return cached;
    }
    
    // Tentar buscar do cache principal
    const mainCache = await caches.open(CACHE_NAME);
    const mainCached = await mainCache.match(request);
    if (mainCached) {

      return mainCached;
    }
    
    // Retornar página offline
    const offlinePage = await mainCache.match('/offline/');
    if (offlinePage) {
      return offlinePage;
    }
    
    // Fallback genérico
    return new Response('Offline - Você está sem conexão com a internet', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/html; charset=utf-8'
      })
    });
  }
}

// Sincronização em background
self.addEventListener('sync', (event) => {

  if (event.tag === 'sync-favorites') {
    event.waitUntil(syncFavorites());
  }
});

async function syncFavorites() {
  try {
    // Implementar lógica de sincronização de favoritos

    // TODO: Sincronizar dados pendentes quando online
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

// Notificações Push (preparado para futuro)
self.addEventListener('push', (event) => {

  const options = {
    body: event.data ? event.data.text() : 'Nova atualização disponível',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'extinct-mammals-notification',
    requireInteraction: false
  };
  
  event.waitUntil(
    self.registration.showNotification('Mamíferos Extintos', options)
  );
});

// Clique em notificação
self.addEventListener('notificationclick', (event) => {

  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

// Mensagens do cliente
self.addEventListener('message', (event) => {

  if (event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
  
  if (event.data.action === 'clearCache') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});
