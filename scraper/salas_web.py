"""Lector genérico de webs de sala: los conciertos que la web de una sala publica con datos estructurados
(schema.org Event en JSON-LD, lo que leen Google y las apps). Sin un lector propio para cada sala: muchas webs de
WordPress (The Events Calendar, Modern Events Calendar…) los publican igual.

No añade conciertos: completa los que ya tenemos de esa sala (mismo día y mismo artista) con lo que dice su web
—hora, precio, enlace de entradas, agotado o cancelado— y los confirma ("lo anuncia la web de la sala"). Nada se
deduce: solo lo que la web dice de ese concierto concreto.
"""
from __future__ import annotations

import html as html_lib
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from .entradas import _artistas, _estado, _eventos_jsonld, _hora, _offer_url, _precio, limpiar, ticketera

# donde suelen estar los conciertos en la web de una sala (la portada primero: muchas los listan ahí)
RUTAS = ["", "agenda/", "conciertos/", "eventos/", "programacion/", "events/", "calendario/"]


def paginas_candidatas(web: str) -> list[str]:
    p = urlsplit(web)
    base = f"{p.scheme or 'https'}://{p.netloc}/"
    return [urljoin(base, r) for r in RUTAS]


def eventos_de_web(html: str, url: str) -> list[dict]:
    """Eventos de la página: {"fecha", "hora", "precio", "entradas", "nombre", "artistas", "estado",
    "disponibilidad", "url"}. Solo los que traen fecha."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for ev in _eventos_jsonld(soup):
        inicio = str(ev.get("startDate") or "")
        if not re.match(r"\d{4}-\d{2}-\d{2}", inicio):
            continue
        nombre = re.sub(r"\s+", " ", html_lib.unescape(str(ev.get("name") or ""))).strip()[:200]
        estado, disp = _estado(ev)
        ou = _offer_url(ev)
        out.append({"fecha": inicio[:10], "hora": _hora(inicio), "precio": _precio(ev.get("offers")),
                    "entradas": limpiar(ou) if ou and ticketera(ou) else None, "nombre": nombre,
                    "artistas": _artistas(ev.get("performer")), "estado": estado, "disponibilidad": disp,
                    "url": urljoin(url, ev["url"]) if isinstance(ev.get("url"), str) else url})
    return out
