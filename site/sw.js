// Copia local de la web y de los últimos datos descargados. Siempre se intenta la red primero (los datos
// cambian cada día); si falla o tarda más de 6 s, se usa la última copia buena. Solo para este mismo sitio.
const CACHE = "agenda-v1";

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
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const red = fetch(req);
      red.catch(() => {});
      const tiempo = new Promise((_, no) => setTimeout(() => no(new Error("tiempo")), 6000));
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
