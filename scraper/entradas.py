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

import json
import re
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
}
_TICKET_HOST = re.compile(r"ticket|entrada|taquilla|tiquet|boleter", re.I)
_TEXTO_COMPRA = re.compile(r"(?i)\b(comprar|compra|entradas?|tickets?|reserva[r]?|buy)\b")
# enlaces que nunca son de compra aunque el dominio lo parezca
_NO = re.compile(r"(?i)/(blog|noticias?|news|ayuda|help|faq|contacto|login|registro|cuenta|account)\b|facebook|instagram|"
                 r"twitter|x\.com|youtube|spotify|whatsapp|mailto:|tel:")


def dominio(url: str | None) -> str:
    h = urlsplit(url or "").netloc.lower()
    return h[4:] if h.startswith("www.") else h


def ticketera(url: str | None) -> str | None:
    """Nombre de la ticketera si la URL es de una página de entradas; None si no."""
    d = dominio(url)
    if not d:
        return None
    for k, v in TICKETERAS.items():
        if d == k or d.endswith("." + k):
            return v
    return d if _TICKET_HOST.search(d.split(":")[0]) else None


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
        clave = href.split("#")[0]
        if clave in vistos:
            continue
        vistos.add(clave)
        texto = a.get_text(" ", strip=True)[:60]
        out.append({"url": clave, "dominio": d, "nombre": nombre, "texto": texto,
                    "compra": bool(_TEXTO_COMPRA.search(texto + " " + " ".join(a.get("class") or [])))})
    # primero los que dicen "comprar/entradas"
    return sorted(out, key=lambda e: not e["compra"])


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
        if ou and dominio(ou) != dominio(url) and ticketera(ou):
            out["entradas_jsonld"] = ou
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
