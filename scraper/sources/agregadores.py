"""Agregadores generales: La Ganzúa, Conciertos por Madrid, Madrid en Vivo, Songkick, Rock and Blog,
Ticketle, Bandsintown, blog de Ticketmaster y Radar Joven."""
from __future__ import annotations

import json
import re
from datetime import date
from urllib.parse import urljoin

from ..fetch import RobotsBlocked
from ..normalize import MESES, MESES_ES, MONTHS_EN, clean, parse_fecha_texto, parse_hora
from .base import Ctx, jsonld_events, ld_to_raw, make, months_in_window, soup_of, text

# ------------------------------------------------------------------ La Ganzúa
LAGANZUA = "https://www.laganzua.net/conciertos/madrid/{mes}-{y}"


def laganzua_parse(html: str, page_url: str, today: date) -> list:
    out = []
    for ev in jsonld_events(soup_of(html)):
        m = re.search(r"concierto de (.+?)\.?\s*$", ev.get("description") or "")
        estilo = clean(m.group(1)) if m else None
        r = ld_to_raw(ev, today, page_url, estilo=estilo)
        if r:
            if norm_sala_vacia(r.sala):
                r.sala = ""
            out.append(r)
    return out


def norm_sala_vacia(s: str) -> bool:
    return bool(re.search(r"(?i)por confirmar|sin confirmar|^tba$|^por determinar", s or ""))


def laganzua(ctx: Ctx):
    for y, m in months_in_window(ctx.today, ctx.horizon):
        base = LAGANZUA.format(mes=MESES_ES[m - 1], y=y)
        seen = set()
        for page in range(1, 40):
            url = base if page == 1 else f"{base}/pagina-{page}"
            try:
                html = ctx.get(url)
            except Exception as e:  # noqa: BLE001
                if "404" in str(e):
                    break
                raise
            evs = laganzua_parse(html, url, ctx.today)
            keys = {(e.url, e.fecha, e.hora) for e in evs}
            if not evs or keys <= seen:
                break
            seen |= keys
            yield from evs


# ------------------------------------------------------------------ Conciertos por Madrid
CPM = "https://conciertospormadrid.com/conciertos-madrid-{mes}/"


def cpm_parse(html: str, page_url: str, today: date) -> list:
    s = soup_of(html)
    out = []
    for li in s.find_all("li"):
        st = li.find("strong")
        a = li.find("a", href=re.compile(r"/conciertos/"))
        if not st or not a or not re.match(r"\d{1,2} \w{3} \d{4}$", text(st)):
            continue
        fecha = parse_fecha_texto(text(st), today)
        if not fecha:
            continue
        nombre = text(a)
        # "<strong>fecha</strong> · <a>ARTISTA</a> · Sala · <a>COMPRAR</a>"; en el bloque por salas la sala
        # es el <h4> anterior
        partes = [clean(p) for p in li.get_text("|", strip=True).split("|")]
        sala = ""
        for p in partes:
            p = p.strip("· ").strip()
            if p and p not in (text(st), nombre) and "COMPRAR" not in p.upper():
                sala = p
                break
        if not sala:
            h4 = li.find_previous("h4")
            sala = text(h4) if h4 else ""
        ciudad = None
        mc = re.match(r"(.*)\(([^)]+)\)\s*$", sala)
        if mc:
            sala, ciudad = clean(mc.group(1)), clean(mc.group(2))
        if re.search(r"(?i)^otro|exterior", sala):
            sala = ""
        out.append(make(fecha, nombre, a["href"], sala=sala, ciudad=ciudad or "Madrid"))
    return out


def conciertospormadrid(ctx: Ctx):
    for y, m in months_in_window(ctx.today, ctx.horizon):
        url = CPM.format(mes=MESES_ES[m - 1])
        for e in cpm_parse(ctx.get(url), url, ctx.today):
            if e.fecha.month == m:
                yield e


# ------------------------------------------------------------------ Madrid en Vivo
MEV_AJAX = "https://madridenvivo.com/wp-content/themes/base/codigo/includes/ajax/buscar-eventos-avanzado.php"
# Se consulta por estilo (así el estilo lo da la propia web). Primero los estilos en foco.
MEV_ESTILOS = {"779": "Pop / Rock", "778": "Músicas negras", "772": "Clubbing", "774": "Flamenco Capital",
               "822": "Musicales", "770": "Artes escénicas"}
MEV_PRESUPUESTO_SEG = 1200  # su servidor responde lento (~10 s por página)


def mev_parse(html: str, page_url: str, today: date, estilo: str | None) -> list:
    s = soup_of(html)
    out = []
    for div in s.select(".info-evento"):
        h2 = div.find("h2")
        spans = div.select("div > span")
        if not h2 or len(spans) < 2:
            continue
        fecha = parse_fecha_texto(text(spans[-1]).split("|")[0], today)
        if not fecha:
            continue
        sala = text(spans[0].find("a")) or re.sub(r"^Sala\s+", "", text(spans[0]))
        a = h2.find_parent("a") or div.find("a", href=True)
        url = urljoin("https://madridenvivo.com/", a["href"]) if a else page_url
        out.append(make(fecha, text(h2), url, sala=sala, ciudad="Madrid", estilo=estilo))
    return out


def madridenvivo(ctx: Ctx):
    """Consulta el buscador avanzado por cada estilo (el estilo sale del filtro de la propia web)
    y paginando la misma petición POST que hace la web al hacer scroll."""
    import time
    t0 = time.monotonic()
    seen: dict[str, object] = {}
    for eid, ename in MEV_ESTILOS.items():
        for page in range(1, 200):
            if time.monotonic() - t0 > MEV_PRESUPUESTO_SEG:
                ctx.errors.append(f"tiempo máximo alcanzado: estilo '{ename}' leído hasta la página {page - 1}")
                return
            payload = {"salas": "", "estilos": eid, "fecha-desde": ctx.today.isoformat(),
                       "fecha-hasta": ctx.horizon.isoformat(), "buscar": "", "pagina": page}
            raw = ctx.get(MEV_AJAX, method="POST", data=json.dumps(payload),
                          headers={"Content-Type": "application/json; charset=UTF-8",
                                   "X-Requested-With": "XMLHttpRequest"})
            try:
                resp = json.loads(raw)
            except ValueError:
                ctx.errors.append(f"respuesta no JSON en página {page} (estilo {ename})")
                break
            if resp.get("status") != 200 or not resp.get("html"):
                break
            evs = mev_parse(resp["html"], "https://madridenvivo.com/buscador-avanzado/", ctx.today, ename)
            if not evs:
                break
            nuevos = 0
            for e in evs:
                k = f"{e.url}|{e.fecha}"
                if k in seen:
                    continue
                seen[k] = e
                nuevos += 1
                yield e
            if nuevos == 0:
                break


# ------------------------------------------------------------------ Songkick
SONGKICK = "https://www.songkick.com/metro-areas/28755-spain-madrid"


def songkick_parse(html: str, page_url: str, today: date) -> list:
    out = []
    for ev in jsonld_events(soup_of(html)):
        perf = ev.get("performer") or []
        perf = perf if isinstance(perf, list) else [perf]
        genres = []
        for p in perf[:1]:
            g = p.get("genre") if isinstance(p, dict) else None
            genres = g if isinstance(g, list) else ([g] if g else [])
        name = clean(ev.get("name"))
        # "Artista @ Sala": Songkick nombra el evento así; el cartel real está en performer
        names = [clean(p.get("name")) for p in perf if isinstance(p, dict) and p.get("name")]
        ev = dict(ev)
        if names:
            ev["name"] = names[0]
        elif " @ " in name:
            ev["name"] = name.split(" @ ")[0]
        if "festival" in (ev.get("@type") or "").lower() or "Festival" in name:
            ev["name"] = name.split(" @ ")[0]
        r = ld_to_raw(ev, today, page_url, estilo=", ".join(genres) or None, split=False)
        if r:
            r.url = (ev.get("url") or page_url).split("?")[0]
            out.append(r)
    return out


def songkick(ctx: Ctx):
    for page in range(1, 60):
        url = SONGKICK if page == 1 else f"{SONGKICK}?page={page}"
        evs = songkick_parse(ctx.get(url), url, ctx.today)
        if not evs:
            break
        yield from evs
        if min(e.fecha for e in evs) > ctx.horizon:
            break


# ------------------------------------------------------------------ Rock and Blog
def rockandblog_parse(html: str, page_url: str, today: date) -> list:
    out = []
    for ev in jsonld_events(soup_of(html)):
        r = ld_to_raw(ev, today, page_url)
        if r:
            out.append(r)
    return out


def rockandblog(ctx: Ctx):
    url = "https://rockandblog.net/conciertos-rock-madrid/"
    yield from rockandblog_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Ticketle
def ticketle_parse(html: str, page_url: str, today: date) -> list:
    out = []
    for ev in jsonld_events(soup_of(html)):
        r = ld_to_raw(ev, today, page_url)
        if r:
            out.append(r)
    return out


def ticketle(ctx: Ctx):
    for y, m in months_in_window(ctx.today, ctx.horizon):
        for page in range(1, 30):
            url = f"https://www.ticketle.es/madrid/{MONTHS_EN[m - 1]}" + (f"?page={page}" if page > 1 else "")
            evs = ticketle_parse(ctx.get(url), url, ctx.today)
            if not evs:
                break
            yield from evs


# ------------------------------------------------------------------ Bandsintown
def bandsintown(ctx: Ctx):
    url = "https://www.bandsintown.com/c/madrid-spain"
    for ev in jsonld_events(ctx.soup(url)):
        r = ld_to_raw(ev, ctx.today, url)
        if r:
            yield r


# ------------------------------------------------------------------ Blog Ticketmaster (agenda rock)
def tm_blog_parse(html: str, page_url: str, today: date) -> list:
    """Estructura: <li><a><strong>Artista</strong></a><ul><li>17 de octubre de 2026, Sala X de <strong>Ciudad</strong>
    </li></ul></li>. Las fechas tachadas (<del>) ya pasaron o se anularon y se ignoran."""
    s = soup_of(html)
    out = []
    for li in s.select("li"):
        head = li.find("strong")
        sub = li.find("ul")
        if not head or not sub or head.find_parent("ul") is not li.find_parent("ul"):
            continue
        artista = text(head)
        artista = re.sub(r"(?i)\s+(en su|en la|con su)\s+gira.*$", "", artista)
        a = head.find_parent("a")
        url = a["href"] if a and a.get("href") else page_url
        for d in sub.find_all("li", recursive=False):
            if d.find("del"):
                continue
            t = text(d)
            m = re.match(r"(\d{1,2})(?:\s*y\s*(\d{1,2}))?\s+de\s+(\w+)\s+de\s+(20\d\d),\s*(.*)$", t)
            if not m or not MESES.get(m.group(3).lower()):
                continue
            ciudad_el = d.find("strong")
            ciudad = text(ciudad_el) if ciudad_el else ""
            sala = clean(re.sub(r"\s+de\s*$", "", m.group(5).replace(ciudad, "").strip()))
            for dd in filter(None, [m.group(1), m.group(2)]):
                try:
                    f = date(int(m.group(4)), MESES[m.group(3).lower()], int(dd))
                except ValueError:
                    continue
                out.append(make(f, artista, page_url, sala=sala, ciudad=ciudad, nota=f"Entradas: {url}"))
    return out


def tm_blog(ctx: Ctx):
    url = "https://blog.ticketmaster.es/post/agenda-rock-2026-38621/"
    yield from tm_blog_parse(ctx.get(url), url, ctx.today)


# ------------------------------------------------------------------ Radar Joven
def radar_joven(ctx: Ctx):
    url = "https://www.comunidad.madrid/actividades/2026/radar-joven-2026"
    s = ctx.soup(url)
    yield from radar_parse(str(s), url, ctx.today)


def radar_parse(html: str, page_url: str, today: date) -> list:
    """Líneas del tipo '15 de octubre. Sala X: Grupo A + Grupo B'."""
    s = soup_of(html)
    out = []
    for el in s.find_all(["p", "li", "td"]):
        t = text(el)
        m = re.match(r"(?:\w+\s+)?(\d{1,2}) de (\w+)(?: de (20\d\d))?[.,:]?\s*[-–·]?\s*(.+?)\s*[:\-–]\s*(.+)$", t)
        if not m or not MESES.get(m.group(2).lower()):
            continue
        f = parse_fecha_texto(f"{m.group(1)} de {m.group(2)} {m.group(3) or ''}", today)
        if f:
            out.append(make(f, m.group(5), page_url, sala=m.group(4), ciudad="Madrid", estilo=None))
    return out
