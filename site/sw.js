// Copia local de la web y de los últimos datos descargados. La web y la agenda: primero la red (cambian cada día);
// si falla o tarda más de 3,5 s, la última copia buena. Detalles y miniaturas: la copia al instante y se
// actualiza por detrás. Solo para este mismo sitio.
const CACHE = "agenda-v4";

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "index.html"])).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  const url = new URL(req.url);
  // detalles de conciertos y miniaturas propias: cambian como mucho una vez al día. Se sirve la copia guardada al
  // instante (si la hay) y se actualiza por detrás para la próxima vez
  if (/\/data\/detalles\/|\/miniaturas\//.test(url.pathname)) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const copia = await cache.match(req);
      const red = fetch(req).then(r => { if (r.ok) cache.put(req, r.clone()); return r; });
      if (copia) { e.waitUntil(red.catch(() => {})); return copia; }
      return red;
    })());
    return;
  }
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const red = fetch(req);
      red.catch(() => {});
      const tiempo = new Promise((_, no) => setTimeout(() => no(new Error("tiempo")), 3500));
      const r = await Promise.race([red, tiempo]);
      if (r.ok) cache.put(req, r.clone());
      return r;
    } catch (err) {
      const copia = await cache.match(req, {ignoreSearch: true});
      if (copia) return copia;
      throw err;
    }
  })());
});
