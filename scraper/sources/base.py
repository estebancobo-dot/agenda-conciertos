"""Utilidades comunes a los parsers."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

from bs4 import BeautifulSoup

from ..fetch import Fetcher
from ..model import RawEvent
from ..normalize import clean, es_relleno, extrae_pais, parse_fecha_texto, parse_hora, split_artistas


@dataclass
class Ctx:
    """Contexto que recibe cada parser."""
    fetcher: Fetcher | None
    today: date
    horizon: date
    estado: dict = field(default_factory=dict)   # estado incremental de esta fuente (se guarda en estado.json)
    pages: int = 0
    errors: list[str] = field(default_factory=list)

    def get(self, url: str, **kw) -> str:
        self.pages += 1
        return self.fetcher.get(url, **kw)

    def soup(self, url: str, **kw) -> BeautifulSoup:
        return BeautifulSoup(self.get(url, **kw), "lxml")

    def in_window(self, d: date | None) -> bool:
        return d is not None and self.today <= d <= self.horizon


def soup_of(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def text(el) -> str:
    return clean(el.get_text(" ", strip=True)) if el is not None else ""


def make(fecha: date, nombre: str, url: str, *, split: bool = True, **kw) -> RawEvent:
    """Crea un RawEvent separando invitados con '+' y el código de país '(XX)' si la fuente lo pone."""
    nombre = clean(nombre)
    invitados = kw.pop("invitados", None)
    if split and invitados is None:
        nombre, invitados = split_artistas(nombre)
    invitados = [clean(i) for i in (invitados or []) if clean(i) and not es_relleno(i)]
    nombre, pais = extrae_pais(nombre)
    if pais and not kw.get("nacionalidad"):
        kw["nacionalidad"] = pais
    invitados = [extrae_pais(i)[0] for i in invitados]
    return RawEvent(fecha=fecha, artista=nombre, url=url, invitados=invitados, **kw)


# ---------------------------------------------------------------- JSON-LD
def jsonld_events(soup: BeautifulSoup) -> list[dict]:
    out = []
    for sc in soup.select('script[type="application/ld+json"]'):
        raw = sc.string or sc.get_text() or ""
        try:
            data = json.loads(raw)
        except ValueError:
            try:
                data = json.loads(re.sub(r"[\x00-\x1f]", " ", raw))
            except ValueError:
                continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, dict):
                t = x.get("@type")
                ts = t if isinstance(t, list) else [t]
                if any(isinstance(y, str) and y.endswith("Event") for y in ts):
                    out.append(x)
                else:
                    stack.extend(v for v in x.values() if isinstance(v, (list, dict)))
    return out


def _first(x):
    return x[0] if isinstance(x, list) and x else x


def ld_to_raw(ev: dict, today: date, page_url: str, *, use_performers: bool = True, split: bool = True,
              estilo: str | None = None) -> RawEvent | None:
    start = ev.get("startDate") or ""
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", start)
    if not m:
        return None
    fecha = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    hora = None
    mt = re.search(r"T(\d{1,2}):(\d{2})", start)
    if mt and not (mt.group(1) == "00" and mt.group(2) == "00"):
        hora = f"{mt.group(1)}:{mt.group(2)}"
    loc = _first(ev.get("location")) or {}
    sala = clean(loc.get("name")) if isinstance(loc, dict) else ""
    addr = loc.get("address") if isinstance(loc, dict) else None
    addr = _first(addr)
    ciudad = None
    if isinstance(addr, dict):
        ciudad = clean(addr.get("addressLocality")) or clean(addr.get("addressRegion")) or None
    elif isinstance(addr, str):
        ciudad = addr
    perf = ev.get("performer")
    perf = perf if isinstance(perf, list) else ([perf] if perf else [])
    names = [clean(p.get("name")) for p in perf if isinstance(p, dict) and clean(p.get("name"))]
    nombre = clean(ev.get("name"))
    invitados = None
    if use_performers and len(names) > 1:
        nombre, invitados = names[0], names[1:]
    offers = _first(ev.get("offers")) or {}
    precio = None
    if isinstance(offers, dict) and offers.get("price") not in (None, "", 0, "0"):
        precio = f"{offers.get('price')} {offers.get('priceCurrency') or ''}".strip()
    url = ev.get("url") or ev.get("@id") or page_url
    img = _first(ev.get("image"))
    if isinstance(img, dict):
        img = img.get("url") or img.get("contentUrl")
    img = img if isinstance(img, str) and img.startswith("http") else None
    return make(fecha, nombre, url, split=split, invitados=invitados, sala=sala, ciudad=ciudad, hora=hora,
                precio=precio, estilo=estilo, imagen=img)


def months_in_window(today: date, horizon: date) -> Iterable[tuple[int, int]]:
    y, m = today.year, today.month
    while (y, m) <= (horizon.year, horizon.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def weeks_in_window(today: date, horizon: date) -> Iterable[tuple[date, date]]:
    d = today
    while d <= horizon:
        e = min(d + timedelta(days=6), horizon)
        yield d, e
        d = e + timedelta(days=1)


__all__ = ["Ctx", "RawEvent", "make", "text", "soup_of", "jsonld_events", "ld_to_raw", "months_in_window",
           "weeks_in_window", "parse_fecha_texto", "parse_hora", "clean"]
