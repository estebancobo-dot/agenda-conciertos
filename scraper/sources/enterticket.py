"""Enterticket (enterticket.es): ticketera de salas como Villanos (cuya web ya no deja leerla en su robots.txt).

Su robots.txt permite /eventos/ y /sitemap.xml. No tiene listado por sala ni por ciudad legible, así que:
1. el sitemap da todas sus páginas de evento (de toda España);
2. de cada página nueva se leen los datos que trae para montarse (__NEXT_DATA__: sala con dirección, fecha y hora en
   hora de Madrid, precio mínimo, artistas, categoría), y se guarda si es un concierto en la Comunidad de Madrid;
3. solo se abren las páginas nuevas (y las de Madrid cada pocos días, por si cambian), con un tope por lectura:
   el resto queda para la siguiente. Lo ya visto se recuerda en estado.json."""
from __future__ import annotations

import html as html_lib
import json
import re
from datetime import date, timedelta

from ..normalize import clean, municipio
from .base import Ctx, TiempoAgotado, make

SITEMAP = "https://www.enterticket.es/sitemap.xml"
MAX_PAGINAS = 150      # páginas de evento por lectura (a 1 por segundo como mínimo)
REVISAR_DIAS = 3       # los conciertos de Madrid se vuelven a mirar cada 3 días (hora, precio, cancelación)
CATEGORIAS = {"conciertos", "festivales"}
# fiestas y sesiones de DJ que la ticketera también llama "conciertos"
_NO_CONCIERTO = re.compile(r"(?i)\b(dj|djs|dj set|brunch|clubbing|club night|fiesta|party|techno|after)\b")
_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
_CIUDAD = re.compile(r"(?i)\s*(?:[-–|]\s*|\ben\s+)(?:madrid|alcal[aá] de henares|getafe|legan[eé]s|m[oó]stoles|"
                     r"fuenlabrada|alcorc[oó]n|torrej[oó]n de ardoz|las rozas)\b.*$")


def evento_de_pagina(html: str, url: str) -> dict | None:
    """Lo que interesa de la página de un evento, o None si no trae datos. 'madrid': concierto en la Comunidad."""
    m = _NEXT.search(html)
    if not m:
        return None
    try:
        ev = json.loads(m.group(1))["props"]["pageProps"]["event"]
    except (ValueError, KeyError, TypeError):
        return None
    venue = ev.get("venue") or {}
    addr = venue.get("address") or {}
    muni = municipio(addr.get("city")) if (addr.get("province") or "").lower() == "madrid" else None
    cat = ((ev.get("category") or {}).get("slug") or "").lower()
    inicio = ((ev.get("start_date") or {}).get("date") or "")[:16]
    nombre_ev = html_lib.unescape(ev.get("name") or "")
    out = {"madrid": bool(muni and cat in CATEGORIAS and inicio and not _NO_CONCIERTO.search(nombre_ev)),
           "fecha": inicio[:10]}
    if not out["madrid"]:
        return out
    hora = inicio[11:16] if inicio[11:16] not in ("", "00:00") else None
    precio = ev.get("minimum_price")
    artistas = [clean(a.get("name")) for a in ev.get("artists") or [] if clean(a.get("name"))]
    nombre = clean(_CIUDAD.sub("", nombre_ev)) or (artistas[0] if artistas else "")
    out.update({"nombre": nombre, "hora": hora, "sala": clean(venue.get("name")), "ciudad": muni, "url": url,
                "precio": f"desde {precio:.2f} €".replace(".", ",") if isinstance(precio, (int, float)) and precio else None,
                "invitados": [a for a in artistas[1:] if a.lower() not in nombre.lower()],
                "activo": bool(ev.get("active", True)) and bool(ev.get("front_active", True))})
    return out


def enterticket(ctx: Ctx):
    xml = ctx.get(SITEMAP)
    urls = list(dict.fromkeys(re.findall(r"<loc>\s*(https://www\.enterticket\.es/eventos/[^<\s]+)\s*</loc>", xml)))
    fichas: dict = ctx.estado.setdefault("fichas", {})
    hoy = ctx.today.isoformat()
    revisar = (ctx.today - timedelta(days=REVISAR_DIAS)).isoformat()
    en_sitemap = {u.rsplit("/", 1)[-1] for u in urls}
    for slug in [s for s in fichas if s not in en_sitemap or (fichas[s].get("fecha") or "9999") < hoy]:
        fichas.pop(slug)  # ya pasó o ya no se vende
    nuevas = [u for u in urls if u.rsplit("/", 1)[-1] not in fichas]
    viejas = [u for u in urls if (f := fichas.get(u.rsplit("/", 1)[-1])) and f.get("madrid") and f.get("visto", "") < revisar]
    # primero las que dicen Madrid en la dirección: casi siempre son de aquí
    nuevas.sort(key=lambda u: "madrid" not in u)
    pendientes = (nuevas + viejas)[:MAX_PAGINAS]
    for u in pendientes:
        slug = u.rsplit("/", 1)[-1]
        try:
            d = evento_de_pagina(ctx.get(u), u)
        except TiempoAgotado:
            break
        except Exception as e:  # noqa: BLE001 - una página que falla no para las demás
            ctx.errors.append(f"{u}: {type(e).__name__}")
            continue
        if d is None:
            continue
        d["visto"] = hoy
        fichas[slug] = d if d["madrid"] else {"madrid": False, "fecha": d["fecha"], "visto": hoy}
    ctx.estado["pendientes"] = max(0, len(nuevas) + len(viejas) - len(pendientes))
    for d in fichas.values():
        if not d.get("madrid") or not d.get("activo", True):
            continue
        f = date.fromisoformat(d["fecha"])
        if ctx.in_window(f):
            yield make(f, d["nombre"], d["url"], split=False, invitados=d.get("invitados") or [], sala=d["sala"],
                       ciudad=d["ciudad"], hora=d.get("hora"), precio=d.get("precio"))
