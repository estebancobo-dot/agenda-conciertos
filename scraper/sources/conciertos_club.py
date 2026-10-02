"""conciertos.club: buscador por semanas, portada de Madrid y páginas por estilo.

Estructura verificada (sep-2026): <ul class="list"><li> con .time ('S17/10/26<br>21:00'), a.nombre,
span.estilo (' / Metal/Rock duro'), a.local[title='Sala, Municipio (Provincia)'], span.precio y, en el
buscador y la portada, microdatos schema.org (performer, startDate).
"""
from __future__ import annotations

import re
from datetime import date
from urllib.parse import urljoin

from .base import Ctx, clean, make, soup_of, text, weeks_in_window

BASE = "https://conciertos.club"
SEARCH = ("https://conciertos.club/search.php?artist_id=&local_id=&provin_id=3&estilo_id="
          "&fecha1={d1}&fecha2={d2}")
ESTILOS = ["americana-folk-rock-country", "blues-rnb", "folk", "pop-rock-indie", "pop", "post-punk",
           "rock-rock-alternativo", "rock-and-roll-garage", "punk-hardcore", "metal-rock-duro", "cantautores",
           "versiones-tributos", "reggae-ska", "world-music-musica-etnica"]

_TIME = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{2})")


def parse_list(html: str, page_url: str) -> list:
    s = soup_of(html)
    out = []
    for li in s.select("ul.list > li"):
        t = li.select_one(".time")
        a = li.select_one("a.nombre")
        if not t or not a:
            continue
        tt = text(t)
        m = _TIME.search(tt)
        if not m:
            continue
        fecha = date(2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))
        hora = None
        mh = re.search(r"(\d{1,2}):(\d{2})\s*$", tt)
        if mh and not (mh.group(1) in ("0", "00") and mh.group(2) == "00"):
            hora = f"{int(mh.group(1)):02d}:{mh.group(2)}"
        md_name = li.select_one(".microdatos > meta[itemprop=name]")
        nombre = clean(md_name["content"]) if md_name else text(a)
        perf = [clean(x["content"]) for x in li.select("[itemprop=performer] meta[itemprop=name]")]
        invitados = None
        if len(perf) > 1:
            nombre, invitados = perf[0], perf[1:]
        estilo = text(li.select_one(".estilo")).lstrip("/ ").strip() or None
        local = li.select_one("a.local")
        sala, ciudad = "", None
        if local is not None:
            title = local.get("title") or ""
            mt = re.match(r"(.*),\s*([^,]+?)\s*\(([^)]+)\)\s*$", title)
            if mt:
                sala, ciudad = clean(mt.group(1)), f"{clean(mt.group(2))} ({clean(mt.group(3))})"
            else:
                raw = text(local)
                sala, _, ciudad = raw.rpartition(". ")
                sala, ciudad = (sala or raw), (ciudad or None)
        precio_el = li.select_one(".precio")
        precio = text(precio_el) or None
        url = urljoin(BASE, a.get("href") or "") or page_url
        img = li.select_one("meta[itemprop=image]")
        imagen = img["content"] if img and img.get("content", "").startswith("http") else None
        if not imagen:
            im = li.select_one(".img img[data-src]")
            imagen = urljoin(BASE, im["data-src"]) if im else None
        out.append(make(fecha, nombre, url, invitados=invitados, sala=sala, ciudad=ciudad, hora=hora,
                        precio=precio, estilo=estilo, imagen=imagen))
    return out


def buscador(ctx: Ctx):
    for d1, d2 in weeks_in_window(ctx.today, ctx.horizon):
        url = SEARCH.format(d1=d1.strftime("%d%%2F%m%%2F%Y"), d2=d2.strftime("%d%%2F%m%%2F%Y"))
        yield from parse_list(ctx.get(url), url)


def portada(ctx: Ctx):
    url = f"{BASE}/madrid"
    yield from parse_list(ctx.get(url), url)


def estilos(ctx: Ctx):
    for e in ESTILOS:
        url = f"{BASE}/madrid/conciertos/estilos/{e}"
        try:
            yield from parse_list(ctx.get(url), url)
        except Exception as ex:  # noqa: BLE001 - un estilo caído no debe tumbar los demás
            ctx.errors.append(f"{url}: {type(ex).__name__}: {ex}")
