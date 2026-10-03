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
# Solo los estilos de conciertos. Se dejan fuera "Artes escénicas" (teatro, monólogos), "Musicales" y
# "Clubbing" (sesiones de DJ): no son conciertos (~10 % de sus actos). Su robots.txt pide 10 s entre
# peticiones (Crawl-delay) y cada página (10 actos) tarda ~9 s más: cada página que se ahorra son ~20 s.
MEV_ESTILOS = {"779": "Pop / Rock", "778": "Músicas negras", "774": "Flamenco Capital"}
MEV_EXCLUIDOS = {"Artes escénicas", "Musicales", "Clubbing"}
MEV_PRESUPUESTO_SEG = 2400


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
        ic = div.select_one(".img-container[style]")
        mi = re.search(r"url\('([^']+)'\)", ic["style"]) if ic else None
        out.append(make(fecha, text(h2), url, sala=sala, ciudad="Madrid", estilo=estilo,
                        imagen=mi.group(1) if mi else None))
    return out


MEV_API = "https://madridenvivo.com/wp-json/wp/v2"
MEV_API_PAGINAS = 12  # 100 eventos por página, los publicados más recientemente primero


def mev_datos_ficha(e, acf: dict) -> None:
    """Hora y precio que la sala puso en la ficha del evento (campos de la API: hora_del_pase, precio_del_evento,
    entrada_libre). El listado del buscador no los trae. Solo si la ficha es del mismo día que el evento."""
    f = str(acf.get("fecha_del_evento") or "")
    if len(f) == 8 and f != e.fecha.strftime("%Y%m%d"):
        return  # evento con varias fechas: la ficha puede ser de otra
    pases = [str(p.get("hora") or "").strip() for p in acf.get("hora_del_pase") or [] if isinstance(p, dict)]
    pases = [h for h in pases if re.fullmatch(r"\d{1,2}:\d{2}", h) and h not in ("00:00",)]
    if pases and not e.hora:
        e.hora = pases[0].zfill(5)
        if len(pases) > 1:
            e.nota = clean(f"{e.nota or ''} Varios pases: {', '.join(pases)}.")
    if not e.precio:
        if acf.get("entrada_libre"):
            e.precio = "Entrada libre"
        elif re.search(r"\d", str(acf.get("precio_del_evento") or "")):
            e.precio = clean(str(acf["precio_del_evento"]))


def mev_estilos_api(ctx: Ctx, eventos: list) -> int:
    """Estilos, hora y precio de cada evento desde la API pública de WordPress de la web ("#Folk-Rock", "#Indie"…;
    hora_del_pase, precio_del_evento: mev_datos_ficha). El buscador
    solo da la categoría ("Pop / Rock", "Músicas negras"); la ficha del evento lleva además sus estilos. Se piden
    en bloques de 100 (con los 10 s entre peticiones que pide su robots.txt) y se ponen como estilo del evento,
    los que se reconocen; la categoría queda si no hay ninguno. Devuelve cuántos eventos se han concretado."""
    from urllib.parse import parse_qs, urlsplit

    from ..clasificar import categorias_de
    por_url = {e.url.rstrip("/"): e for e in eventos}
    por_id = {}
    for e in eventos:
        q = parse_qs(urlsplit(e.url).query)
        if q.get("p"):
            por_id[q["p"][0]] = e
    etiquetas: dict[int, list] = {}
    vistos: set[int] = set()
    for page in range(1, MEV_API_PAGINAS + 1):
        try:
            lote = json.loads(ctx.get(f"{MEV_API}/evento?per_page=100&page={page}&_fields=id,link,tags,acf"))
        except Exception as ex:  # noqa: BLE001 - sin la API se queda la categoría, como antes
            ctx.errors.append(f"estilos por la API: página {page}: {type(ex).__name__}")
            break
        if not isinstance(lote, list) or not lote:
            break
        for ev in lote:
            e = por_url.get(str(ev.get("link") or "").rstrip("/")) or por_id.get(str(ev.get("id")))
            if e is None:
                continue
            vistos.add(id(e))
            mev_datos_ficha(e, ev.get("acf") or {})
            if ev.get("tags"):
                etiquetas[id(e)] = (e, ev["tags"])
        if len(vistos) >= len(eventos):
            break
    ids = sorted({t for _, ts in etiquetas.values() for t in ts})
    nombres: dict[int, str] = {}
    for i in range(0, len(ids), 100):
        try:
            for t in json.loads(ctx.get(f"{MEV_API}/tags?include={','.join(map(str, ids[i:i + 100]))}"
                                        f"&per_page=100&_fields=id,name")):
                nombres[t["id"]] = t["name"]
        except Exception as ex:  # noqa: BLE001
            ctx.errors.append(f"nombres de estilos por la API: {type(ex).__name__}")
    n = 0
    for e, ts in etiquetas.values():
        estilos = []
        for t in ts:
            nombre = re.sub(r"^#", "", str(nombres.get(t, ""))).replace("-", " ").strip()
            if nombre and any(c != "sin clasificar" for c in categorias_de(nombre)) and nombre not in estilos:
                estilos.append(nombre)
        if estilos:
            e.estilo = ", ".join(estilos[:4])
            n += 1
    return n


def madridenvivo(ctx: Ctx):
    """Consulta el buscador avanzado por cada estilo (el estilo sale del filtro de la propia web)
    y paginando la misma petición POST que hace la web al hacer scroll. Después, los estilos concretos de cada
    evento por la API de la web (mev_estilos_api)."""
    import time
    t0 = time.monotonic()
    seen: dict[str, object] = {}
    leidos = list(_madridenvivo_buscador(ctx, t0, seen))
    try:
        mev_estilos_api(ctx, leidos)
    except Exception as ex:  # noqa: BLE001 - nunca impide dar los eventos con su categoría
        ctx.errors.append(f"estilos por la API: {type(ex).__name__}: {str(ex)[:120]}")
    yield from leidos


def _madridenvivo_buscador(ctx: Ctx, t0: float, seen: dict):
    import time
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
        # "Artista @ Sala": Songkick nombra el evento así; el cartel real está en performer (a veces con varios
        # nombres en uno separados por ";")
        names = [n for p in perf if isinstance(p, dict) and p.get("name")
                 for n in (clean(x) for x in str(p["name"]).split(";")) if n]
        ev = dict(ev)
        url = (ev.get("url") or page_url).split("?")[0]
        # festival (su página es /festivals/…): el nombre es el del festival y todos los artistas son su cartel;
        # el primero de la lista no es el cabeza de cartel
        festival = "/festivals/" in url or "festival" in str(ev.get("@type") or "").lower()
        if festival:
            ev["name"] = name.split(" @ ")[0]
        elif names:
            ev["name"] = names[0]
        elif " @ " in name:
            ev["name"] = name.split(" @ ")[0]
        r = ld_to_raw(ev, today, page_url, estilo=", ".join(genres) or None, split=False, use_performers=False)
        if r:
            r.url = url
            # mismos retoques que el resto de invitados (sin relleno ni el "(UK)" del país)
            r.invitados = make(r.fecha, "-", url, invitados=names if festival else names[1:], split=False).invitados
            r.tipo = "festival" if festival else None
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


# ------------------------------------------------------------------ Radar Joven (programación en Conciertos por Madrid)
RADAR_CPM = "https://conciertospormadrid.com/festivales/radar-joven-2026-ciclo-conciertos-madrid/"


def radar_cpm_parse(html: str, page_url: str, today: date) -> list:
    """Líneas 'DD/MM/AAAA: Artista + Artista (Sala)'."""
    s = soup_of(html)
    out = []
    texto = (s.find("article") or s.body).get_text("\n", strip=True)
    for m in re.finditer(r"(\d{2})/(\d{2})/(20\d\d):\s*(.+?)\s*\(([^()]+)\)\s*$", texto, re.M):
        try:
            f = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        out.append(make(f, m.group(4), page_url, sala=clean(m.group(5)), ciudad="Madrid",
                        nota="Ciclo Radar Joven 2026 (Comunidad de Madrid y Madrid en Vivo)."))
    return out


def radar_cpm(ctx: Ctx):
    yield from radar_cpm_parse(ctx.get(RADAR_CPM), RADAR_CPM, ctx.today)
