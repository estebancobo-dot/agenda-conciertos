"""Páginas de concierto y de entradas: lo que dicen del concierto concreto (no del artista).

De la página de un concierto (web de la sala, agenda, ticketera) se saca, solo si la página lo dice:
  - hora de comienzo y precio (datos estructurados schema.org/Event, los que leen Google y las apps);
  - si está agotado, cancelado o aplazado (offers.availability, eventStatus);
  - la imagen oficial del concierto (el cartel de la gira), del JSON-LD o de og:image;
  - los enlaces a páginas de entradas (ticketeras conocidas o dominios con "ticket"/"entradas").

Nada se deduce: si la página no lo dice, no hay dato. El JSON-LD solo cuenta si es del mismo día que el concierto
(una página de sala puede listar varios conciertos).
"""
from __future__ import annotations

import html as html_lib
import json
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

# ticketeras conocidas (dominio → nombre que se enseña). Cualquier otro dominio con "ticket", "entrada",
# "taquilla" o "tiquet" en el nombre también cuenta como página de entradas.
TICKETERAS = {
    "entradas.com": "Entradas.com", "ticketmaster.es": "Ticketmaster", "ticketmaster.com": "Ticketmaster",
    "dice.fm": "DICE", "link.dice.fm": "DICE", "wegow.com": "Wegow", "entradium.com": "Entradium",
    "giglon.com": "Giglon", "eventbrite.es": "Eventbrite", "eventbrite.com": "Eventbrite",
    "feverup.com": "Fever", "taquilla.com": "Taquilla.com", "bipbipticket.com": "BipBip Ticket",
    "mutick.com": "Mutick", "seetickets.com": "See Tickets", "notikumi.com": "Notikumi",
    "woutick.com": "Woutick", "koobin.com": "Koobin", "oneboxtds.com": "OneBox", "proticketing.com": "Proticketing",
    "livenation.es": "Live Nation", "elcorteingles.es": "El Corte Inglés", "universe.com": "Universe",
    "ticketswap.com": "TicketSwap", "compralaentrada.com": "Compralaentrada", "ticketib.com": "Ticketib",
    "entradasatualcance.com": "Entradas a tu alcance", "tickentradas.com": "Tickentradas",
    "madnesslive.es": "Madness Live", "redentradas.com": "Redentradas", "ataquilla.com": "Ataquilla",
    "janto.es": "Janto", "auditorionacional.inaem.gob.es": "INAEM", "entradasinaem.es": "INAEM",
    "movingtickets.com": "Movingtickets", "ticketandroll.com": "Ticket&Roll", "enterticket.es": "Enterticket",
    "enterticket.com": "Enterticket", "jfpromotickets.es": "JF Promotickets", "geeticket.com": "Geeticket",
    "ticketgate.es": "Ticketgate", "tomaticket.es": "Tomaticket", "codetickets.com": "Codetickets",
    "ticketfever.es": "Ticketfever", "ticketrey.com": "Ticketrey", "entradas.conciertos.club": "conciertos.club",
    "ticketmaster.evyy.net": "Ticketmaster", "ticketmaster-es.tm7508.net": "Ticketmaster", "tixxlab.com": "Tixxlab",
    "metaltickets.eu": "Metaltickets", "passline.com": "Passline", "onelivemedia.com": "One Live Media",
}
_TICKET_HOST = re.compile(r"ticket|entrada|taquilla|tiquet|boleter", re.I)
_TEXTO_COMPRA = re.compile(r"(?i)\b(comprar|compra|entradas?|tickets?|reserva[r]?|buy)\b")
# enlaces que nunca son de compra aunque el dominio lo parezca
_NO = re.compile(r"(?i)/(blog|post|noticias?|news|ayuda|help|faq|contact[oa]?|info|login|registro|cuenta|account|legal|"
                 r"aviso-legal|privacidad|privacy|cookies|condiciones|terms|about|quienes-somos|nosotros|empleo|jobs)\b|"
                 r"//blog\.|facebook|instagram|twitter|x\.com|youtube|spotify|whatsapp|mailto:|tel:")
# parámetros de seguimiento que no cambian la página
_RASTREO = re.compile(r"(?i)^(utm_\w+|_gl|gclid|fbclid|srsltid|mc_[ce]id|_ga)$")
# imágenes que no son un cartel: logos, imagen por defecto de la web, la de compartir de la ticketera
_NO_CARTEL = re.compile(r"(?i)logo|default|placeholder|no[-_]?image|sin[-_]?imagen|fallback|og[-_]?image|share|"
                        r"/prod/images/[a-z]+\.(jpe?g|png)$")


def limpiar(u: str | None) -> str | None:
    """Sin fragmento ni parámetros de seguimiento (utm_, _gl, srsltid…)."""
    if not u:
        return u
    from urllib.parse import parse_qsl, urlencode, urlunsplit
    p = urlsplit(u.split("#")[0])
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _RASTREO.match(k)]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), ""))


def dominio(url: str | None) -> str:
    h = urlsplit(url or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def ticketera(url: str | None) -> str | None:
    """Nombre de la ticketera si la URL es de una página de entradas; None si no."""
    d = dominio(url)
    if not d:
        return None
    for k, v in sorted(TICKETERAS.items(), key=lambda kv: -len(kv[0])):
        if d == k or d.endswith("." + k):
            return v
    if not _TICKET_HOST.search(d.split(":")[0]):
        return None
    partes = [x for x in d.split(":")[0].split(".")[:-1] if x not in ("www", "tickets", "ticket", "entradas", "venta", "ventas")]
    return (partes[-1] if partes else d).capitalize()


def _eventos_jsonld(soup: BeautifulSoup) -> list[dict]:
    out: list[dict] = []

    def visitar(x):
        if isinstance(x, list):
            for y in x:
                visitar(y)
        elif isinstance(x, dict):
            t = x.get("@type")
            tipos = t if isinstance(t, list) else [t]
            if any(isinstance(z, str) and z.endswith("Event") for z in tipos):
                out.append(x)
            for k in ("@graph", "itemListElement", "item", "subEvent", "event"):
                if k in x:
                    visitar(x[k])
    for s in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        txt = (s.string or s.get_text() or "").strip()
        if not txt:
            continue
        try:
            visitar(json.loads(txt))
        except ValueError:
            # algunos JSON-LD llevan comas de más o varios objetos seguidos: se prueba objeto a objeto
            for m in re.finditer(r"\{.*?\}(?=\s*(?:,\s*)?\{|\s*\]?\s*$)", txt, re.S):
                try:
                    visitar(json.loads(m.group(0)))
                except ValueError:
                    pass
    return out


def _hora(start: str | None) -> str | None:
    m = re.match(r"\d{4}-\d{2}-\d{2}[T ](\d{2}):(\d{2})", str(start or ""))
    if not m or m.group(0)[11:16] == "00:00":  # 00:00 suele ser "sin hora" en los datos estructurados
        return None
    return f"{m.group(1)}:{m.group(2)}"


def _num(v) -> float | None:
    try:
        n = float(str(v).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return n if 0 < n < 2000 else None


def _precio(offers) -> str | None:
    lista = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
    nums = []
    for o in lista:
        if not isinstance(o, dict):
            continue
        for k in ("price", "lowPrice", "highPrice"):
            n = _num(o.get(k))
            if n is not None:
                nums.append(n)
        if isinstance(o.get("priceSpecification"), dict):
            n = _num(o["priceSpecification"].get("price"))
            if n is not None:
                nums.append(n)
    if not nums:
        return None
    fmt = lambda n: (f"{n:.2f}".rstrip("0").rstrip(".")).replace(".", ",") + " €"  # noqa: E731
    lo, hi = min(nums), max(nums)
    return fmt(lo) if lo == hi else f"{fmt(lo)} – {fmt(hi)}"


def _estado(ev: dict) -> tuple[str | None, str | None]:
    """(estado del evento, disponibilidad): ("cancelado"|"aplazado"|None, "agotado"|"a la venta"|None)."""
    st = str(ev.get("eventStatus") or "")
    estado = "cancelado" if "Cancel" in st else "aplazado" if ("Postpon" in st or "Rescheduled" in st) else None
    offers = ev.get("offers")
    lista = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
    disp = [str(o.get("availability") or "") for o in lista if isinstance(o, dict)]
    if disp and all("SoldOut" in d for d in disp):
        return estado, "agotado"
    if any(re.search(r"InStock|LimitedAvailability|PreOrder|PreSale|OnlineOnly", d) for d in disp):
        return estado, "a la venta"
    return estado, None


def _imagen(x) -> str | None:
    if isinstance(x, list):
        x = x[0] if x else None
    if isinstance(x, dict):
        x = x.get("url") or x.get("contentUrl")
    return x if isinstance(x, str) and x.startswith(("http", "/")) else None


def _offer_url(ev: dict) -> str | None:
    offers = ev.get("offers")
    lista = offers if isinstance(offers, list) else [offers] if isinstance(offers, dict) else []
    for o in lista:
        if isinstance(o, dict) and isinstance(o.get("url"), str) and o["url"].startswith("http"):
            return o["url"]
    return None


def enlaces_entradas(soup: BeautifulSoup, url: str) -> list[dict]:
    """Enlaces de la página a otra web de entradas (no a la propia web)."""
    propio = dominio(url)
    out, vistos = [], set()
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"].strip())
        if not href.startswith("http") or _NO.search(href):
            continue
        d = dominio(href)
        if not d or d == propio:
            continue
        nombre = ticketera(href)
        if not nombre:
            continue
        clave = limpiar(href)
        if clave in vistos:
            continue
        vistos.add(clave)
        texto = a.get_text(" ", strip=True)[:60]
        out.append({"url": clave, "dominio": d, "nombre": nombre, "texto": texto,
                    "compra": bool(_TEXTO_COMPRA.search(texto + " " + " ".join(a.get("class") or [])))})
    # primero los que dicen "comprar/entradas"
    return sorted(out, key=lambda e: not e["compra"])


def _artistas(perf) -> list[str]:
    """Nombres de los performer del JSON-LD (una persona o grupo, o una lista), sin repetir."""
    perf = perf if isinstance(perf, list) else [perf] if perf else []
    out: list[str] = []
    for p in perf:
        n = p.get("name") if isinstance(p, dict) else p if isinstance(p, str) else None
        n = re.sub(r"\s+", " ", html_lib.unescape(str(n or ""))).strip()
        if n and n.lower() not in {x.lower() for x in out} and len(n) <= 120:
            out.append(n)
    return out


def leer_pagina(html: str, url: str, fecha: str | None = None) -> dict:
    """Lo que dice una página de concierto. `fecha` (AAAA-MM-DD): solo vale el JSON-LD de ese día."""
    soup = BeautifulSoup(html, "html.parser")
    evs = _eventos_jsonld(soup)
    if fecha:
        del_dia = [e for e in evs if str(e.get("startDate") or "")[:10] == fecha]
    else:
        del_dia = evs[:1]
    out: dict = {"url": url, "jsonld": bool(evs), "jsonld_del_dia": bool(del_dia)}
    if len(del_dia) == 1 or (del_dia and len({str(e.get("startDate")) for e in del_dia}) == 1):
        ev = del_dia[0]
        out["hora"] = _hora(ev.get("startDate"))
        out["precio"] = _precio(ev.get("offers"))
        out["estado"], out["disponibilidad"] = _estado(ev)
        img = _imagen(ev.get("image"))
        out["imagen"] = urljoin(url, img) if img else None
        ou = _offer_url(ev)
        if ou and dominio(ou) != dominio(url) and ticketera(ou) and not _NO.search(ou):
            out["entradas_jsonld"] = limpiar(ou)
        # cartel: los artistas (performer) en el orden de la página, y el nombre y tipo del evento
        out["cartel"] = _artistas(ev.get("performer"))
        out["evento_nombre"] = html_lib.unescape(str(ev.get("name") or "")).strip()[:200] or None
        t = ev.get("@type")
        out["evento_tipo"] = ",".join(t) if isinstance(t, list) else t
    og = soup.find("meta", attrs={"property": "og:image"}) or soup.find("meta", attrs={"name": "og:image"})
    if og and og.get("content"):
        out["og_imagen"] = urljoin(url, og["content"].strip())
    out["enlaces"] = enlaces_entradas(soup, url)
    return {k: v for k, v in out.items() if v not in (None, [], "")} | {"url": url}


def imagenes_genericas(recs: list[dict], minimo: int = 3) -> set[str]:
    """Imágenes de relleno: la misma URL en conciertos de artistas distintos (la de "evento privado" de una
    agenda, el logo de la sala…). La misma imagen en varias funciones del mismo espectáculo sí es su cartel."""
    from .normalize import norm
    por_url: dict[str, set[str]] = {}
    for r in recs:
        for u in ((r.get("imagen_evento") or {}).get("url"), (r.get("gira") or {}).get("imagen")):
            if u:
                por_url.setdefault(u, set()).add(norm(r.get("artista"))[:20])
    return {u for u, arts in por_url.items() if len(arts) >= minimo}


# ------------------------------------------------------------------ lectura incremental (pasadas de fichas)
# Madrid en Vivo pide 10 s entre peticiones y su página de evento casi nunca enlaza a las entradas: no compensa
NO_LEER = {"madridenvivo"}
# entre páginas de agregador, las que mejor dicen hora/precio (diagnóstico de entradas, oct. 2026)
ORDEN = ["mutick", "laganzua", "songkick", "cc_buscador", "cc_estilos", "cc_portada", "cpm"]
MAX_ENLACES = 6   # una página con más enlaces a entradas es un listado (agenda entera): no son de este concierto
CADUCA_CERCA, CADUCA_LEJOS, CERCA_DIAS, OLVIDAR_DIAS = 3, 10, 14, 30


def sin_fragmento(u: str) -> str:
    return (u or "").split("#")[0]


def _especifica(u: str | None) -> bool:
    """Una URL de compra concreta, no la portada de la ticketera."""
    p = urlsplit(u or "")
    return bool(p.netloc) and p.path.strip("/") != ""


def paginas_de(r: dict, usos: Counter) -> list[tuple[str, dict]]:
    """Páginas propias de este concierto (no listados) en orden de preferencia: web de la sala, luego agregadores."""
    out = []
    for x in r.get("fuentes") or []:
        u = sin_fragmento(x.get("url"))
        if not u.startswith("http") or usos[u] != 1 or x.get("id") in NO_LEER:
            continue
        out.append((u, x))
    orden = {k: i for i, k in enumerate(ORDEN)}
    return sorted(out, key=lambda ux: (ux[1].get("prioridad", 9) != 1, orden.get(ux[1].get("id"), 50)))


def con_huecos(r: dict) -> bool:
    """Le falta algo que una página del concierto puede dar: hora, precio, enlace de entradas o confirmación."""
    return (not r.get("hora") or not r.get("precio") or not r.get("entradas")
            or (r.get("confianza") or {}).get("nivel") == "sin confirmar")


def _caducada(e: dict | None, fecha: str, hoy: date) -> bool:
    if not e:
        return True
    dias = CADUCA_CERCA if (date.fromisoformat(fecha) - hoy).days <= CERCA_DIAS else CADUCA_LEJOS
    return e.get("fecha", "") < (hoy - timedelta(days=dias)).isoformat()


def _resumen(d: dict) -> dict:
    """Lo que se guarda de una página (la caché va a la rama de datos: sin texto ni listas largas)."""
    enl = d.get("enlaces") or []
    out = {k: d[k] for k in ("hora", "precio", "disponibilidad", "estado", "imagen", "og_imagen", "entradas_jsonld")
           if d.get(k)}
    if enl and len(enl) <= MAX_ENLACES:
        out["enlaces"] = [{k: e[k] for k in ("url", "nombre", "compra")} for e in enl[:3]]
    return out


def destino_compra(d: dict) -> str | None:
    """La página de entradas de este concierto que dice una página: la del JSON-LD o el enlace de compra."""
    for u in [d.get("entradas_jsonld")] + [e["url"] for e in sorted(d.get("enlaces") or [], key=lambda e: not e["compra"])]:
        if u and _especifica(u):
            return u
    return None


def leer_entradas(recs: list[dict], cache: dict, fetcher, hoy: date, presupuesto_seg: float,
                  max_workers: int = 8) -> dict:
    """Lee (o vuelve a leer, si caducó) la página de cada concierto próximo y la de entradas que enlace, empezando por
    los más cercanos, hasta agotar el tiempo. Todo lo leído va a `cache` {url: {"fecha", "d"|"error"}}."""
    from .fetch import RobotsBlocked
    fin = time.monotonic() + max(0.0, presupuesto_seg)
    hoy_s = hoy.isoformat()
    # primero los conciertos con huecos (sin hora, precio, enlace de entradas o confirmación): ahí es donde una página
    # más aporta; después, los demás por fecha
    futuros = sorted((r for r in recs if r["fecha"] >= hoy_s), key=lambda r: (not con_huecos(r), r["fecha"]))
    usos = Counter(sin_fragmento(x.get("url")) for r in recs for x in r.get("fuentes") or [] if x.get("url"))
    stats = Counter()
    fallos_dom: Counter = Counter()

    def leer(url: str, fecha: str) -> dict | None:
        if time.monotonic() > fin or fallos_dom[dominio(url)] >= 3:
            return None
        try:
            d = _resumen(leer_pagina(fetcher.get(url), url, fecha))
            cache[url] = {"fecha": hoy_s, "d": d}
            stats["leidas"] += 1
            return d
        except RobotsBlocked:
            cache[url] = {"fecha": hoy_s, "error": "robots.txt no lo permite"}
        except Exception as e:  # noqa: BLE001 (una web caída o que bloquea no para nada)
            cache[url] = {"fecha": hoy_s, "error": f"{type(e).__name__}"[:60]}
            fallos_dom[dominio(url)] += 1
        stats["errores"] += 1
        return None

    def tarea(r: dict) -> None:
        pags = paginas_de(r, usos)
        # la web de la sala (si la hay) y, si no, la mejor página de agenda; con huecos, hasta 3 webs distintas
        elegidas = [p for p in pags if p[1].get("prioridad") == 1][:1] or pags[:1]
        if con_huecos(r):
            webs = {dominio(u) for u, _ in elegidas}
            for u, x in pags:
                if len(elegidas) >= 3:
                    break
                if dominio(u) not in webs:
                    elegidas.append((u, x))
                    webs.add(dominio(u))
        for u, _ in elegidas:
            d = cache.get(u, {}).get("d") if not _caducada(cache.get(u), r["fecha"], hoy) else leer(u, r["fecha"])
            t = destino_compra(d or {})
            if t and ticketera(t) and _caducada(cache.get(t), r["fecha"], hoy):
                leer(t, r["fecha"])

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        list(ex.map(tarea, futuros))
    # se olvida lo que ya no es de ningún concierto próximo ni se ha leído en un mes
    vivas = {sin_fragmento(x.get("url")) for r in futuros for x in r.get("fuentes") or []}
    viejo = (hoy - timedelta(days=OLVIDAR_DIAS)).isoformat()
    for u in [u for u, e in cache.items() if u not in vivas and e.get("fecha", "") < viejo]:
        del cache[u]
    stats["en_cache"] = len(cache)
    return dict(stats)


# ------------------------------------------------------------------ aplicar a los conciertos
def _num_precio(p: str | None) -> float | None:
    m = re.search(r"\d+(?:[.,]\d+)?", str(p or ""))
    return float(m.group(0).replace(",", ".")) if m else None


def _paginas_leidas(r: dict, cache: dict) -> list[tuple[str, dict, str]]:
    """(url, datos, nombre) de las páginas leídas de este concierto y de las de entradas que enlazan."""
    out = []
    for x in r.get("fuentes") or []:
        u = sin_fragmento(x.get("url"))
        d = (cache.get(u) or {}).get("d")
        if d is None:
            continue
        out.append((u, d, x.get("nombre", dominio(u)).split(" (")[0]))
        t = destino_compra(d)
        td = (cache.get(t) or {}).get("d") if t else None
        if td is not None:
            out.insert(0, (t, td, ticketera(t) or dominio(t)))  # la página de entradas, primero
    return out


def confianza(recs: list[dict], cache: dict) -> dict[str, dict]:
    """Por web: ¿su hora y su precio coinciden con los que ya sabemos por otras fuentes? (≥80 % en ≥3 casos). Hay
    webs que ponen "20:00" a todo en sus datos estructurados: así se quedan fuera solas."""
    h, p = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for r in recs:
        for u, d, _ in _paginas_leidas(r, cache):
            dom = dominio(u)
            if d.get("hora") and r.get("hora") and not r.get("hora_pagina"):
                h[dom][0] += d["hora"] == r["hora"]
                h[dom][1] += 1
            a, b = _num_precio(d.get("precio")), _num_precio(r.get("precio"))
            if a is not None and b is not None and not (r.get("precio_fuente") or {}).get("pagina"):
                p[dom][0] += abs(a - b) <= 0.6
                p[dom][1] += 1
    doms = set(h) | set(p)
    ok = lambda c: c[1] >= 3 and c[0] / c[1] >= 0.8  # noqa: E731
    return {d: {"hora": ok(h[d]), "precio": ok(p[d]), "n_hora": h[d][1], "n_precio": p[d][1]} for d in doms}


def aplicar_entradas(recs: list[dict], cache: dict) -> dict:
    """Entradas, hora/precio que falten, agotado/cancelado y cartel de la gira, a partir de las páginas leídas.
    Idempotente: lo que se puso en una pasada anterior se quita y se vuelve a calcular con la regla actual."""
    conf = confianza(recs, cache)
    genericas = imagenes_genericas(recs)
    usos = Counter(sin_fragmento(x.get("url")) for r in recs for x in r.get("fuentes") or [] if x.get("url"))
    c = Counter()
    for r in recs:
        # deshacer lo de pasadas anteriores
        hp = r.pop("hora_pagina", None)
        if hp and r.get("hora") == hp.get("hora"):
            r["hora"] = None
        if (r.get("precio_fuente") or {}).get("pagina"):
            r["precio"], r["precio_fuente"] = None, None
        for k in ("entradas", "agotado", "estado_evento", "gira"):
            r.pop(k, None)
        pags = _paginas_leidas(r, cache)
        # enlace de compra: la fuente que ya es una ticketera; si no, el que dan las páginas
        ent = next(({"url": limpiar(x["url"]), "nombre": ticketera(x["url"]), "via": x.get("nombre", "").split(" (")[0]}
                    for x in r.get("fuentes") or [] if ticketera(x.get("url")) and _especifica(x.get("url"))
                    and usos[sin_fragmento(x["url"])] == 1 and not _NO.search(x["url"])), None)
        if not ent:
            for u, d, nombre in pags:
                t = destino_compra(d) if not ticketera(u) else None
                if t and not _NO.search(t):
                    ent = {"url": t, "nombre": ticketera(t), "via": nombre}
                    break
        if ent:
            r["entradas"] = ent
            c["entradas"] += 1
        hora_conflicto = any(x.get("campo") == "hora" for x in r.get("conflictos") or [])
        for u, d, nombre in pags:
            cf = conf.get(dominio(u), {})
            if not r.get("hora") and not hora_conflicto and d.get("hora") and cf.get("hora"):
                r["hora"], r["hora_pagina"] = d["hora"], {"hora": d["hora"], "nombre": nombre, "url": u}
                c["hora"] += 1
            if not r.get("precio") and d.get("precio") and cf.get("precio"):
                r["precio"], r["precio_fuente"] = d["precio"], {"nombre": nombre, "url": u, "pagina": True}
                c["precio"] += 1
            if d.get("disponibilidad") == "agotado" and "agotado" not in r:
                r["agotado"] = {"nombre": nombre, "url": u}
                c["agotado"] += 1
            if d.get("estado") and "estado_evento" not in r:
                r["estado_evento"] = {"tipo": d["estado"], "nombre": nombre, "url": u}
                c[d["estado"]] += 1
        # cartel de la gira: solo el que publica la sala, la promotora o la página de entradas (las agendas generales
        # ponen a menudo la foto de perfil del artista). Nunca una imagen de relleno ni la foto que ya se enseña.
        ya = (r.get("imagen") or {}).get("url")
        oficiales = {sin_fragmento(x.get("url")) for x in r.get("fuentes") or [] if x.get("prioridad") in (1, 2)}
        cands = [(d.get("imagen") or d.get("og_imagen"), nombre, u) for u, d, nombre in pags
                 if ticketera(u) or u in oficiales]
        ie = r.get("imagen_evento") or {}
        if sin_fragmento(ie.get("enlace")) in oficiales:
            cands.append((ie.get("url"), (ie.get("credito") or "").split(" (")[0], ie.get("enlace")))
        for img, nombre, u in cands:
            if img and img not in genericas and img != ya and img.startswith("http") and not _NO_CARTEL.search(img):
                r["gira"] = {"imagen": img, "credito": nombre, "enlace": u}
                c["gira"] += 1
                break
    # un enlace de compra que les sale a varios artistas distintos no es de ningún concierto concreto (la página de
    # conciertos.club enlaza a veces el primer evento de la sala: Al Di Meola → "Gumbo Jam"): no se enseña ni cuenta
    from .normalize import norm
    artistas_por_url: dict[str, set] = {}
    for r in recs:
        u = (r.get("entradas") or {}).get("url")
        if u:
            artistas_por_url.setdefault(u, set()).add(norm(r.get("artista")))
    genericos = {u for u, a in artistas_por_url.items() if len(a) > 1}
    for r in recs:
        if (r.get("entradas") or {}).get("url") in genericos:
            r.pop("entradas")
            c["entradas"] -= 1
            c["entradas_genericas"] += 1
    c["webs_fiables_hora"] = sum(v["hora"] for v in conf.values())
    return dict(c)
